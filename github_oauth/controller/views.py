import uuid

from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response

from account.service.account_service_impl import AccountServiceImpl
from github_oauth.serializers.github_oauth_access_token_serializer import GithubOauthAccessTokenSerializer
from github_oauth.serializers.github_oauth_url_serializer import GithubOauthUrlSerializer
from github_oauth.service.github_oauth_service_impl import GithubOauthServiceImpl
from github_oauth.service.redis_service_impl import RedisServiceImpl


class OauthView(viewsets.ViewSet):
    githubOauthService = GithubOauthServiceImpl.getInstance()
    accountService = AccountServiceImpl.getInstance()
    redisService = RedisServiceImpl.getInstance()

    def githubOauthURI(self, request):
        url = self.githubOauthService.githubLoginAddress()
        print(f"url: {url}")
        serializer = GithubOauthUrlSerializer(data={'url': url})
        serializer.is_valid(raise_exception=True)
        print(f"validated_data: {serializer.validated_data}")
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    def githubAccessTokenURL(self, request):
        serializer = GithubOauthAccessTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']

        try:
            accessToken = self.githubOauthService.requestAccessToken(code)
            userInfo = self.githubOauthService.requestUserInfo(accessToken['access_token'])

            account = self.accountService.saveUserNickname(userInfo['login'])

            userToken = self.redisAccessToken(account, userInfo['login'], accessToken['access_token'])

            return Response({"userToken": userToken}, status=status.HTTP_200_OK)
        except Exception as e:
            print("e:", e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 위 함수와 통합
    # def githubUserInfoURL(self, request):
    #     accessToken = request.data.get('access_token')
    #     print(f'accessToken: {accessToken}')
    #
    #     try:
    #         userInfo = self.githubOauthService.requestUserInfo(accessToken)
    #         return Response({'user_info': userInfo}, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            username = request.data.get('username')
            access_token = request.data.get('accessToken')
            print(f"redisAccessToken -> username: {username}")

            account = self.accountService.findAccountByUsername(username)
            if not account:
                return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)

            userToken = str(uuid.uuid4())
            self.redisService.store_access_token(account.id, userToken)
            self.redisService.store_access_token(access_token, account.id)


            return Response({'userToken': userToken}, status=status.HTTP_200_OK)
        except Exception as e:
            print('Error storing access token in Redis:', e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def getRedisAccessToken(self, request):
        try:
            userToken = request.data.get('userToken')
            accountId = self.redisService.getValueByKey(userToken)
            print(f"accountId: {accountId}")

            accessToken = self.redisService.getValueByKey(accountId)

            return Response({"accessToken": accessToken}, status=status.HTTP_200_OK)
        except Exception as e:
            print("Error getting access token in Redis:", e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def dropRedisTokenForLogout(self, request):
        try:
            userToken = request.data.get('userToken')

            accountId = self.redisService.getValueByKey(userToken)
            accessToken = self.redisService.getValueByKey(accountId)

            userSuccess = self.redisService.deleteKey(userToken)
            accessSuccess = self.redisService.deleteKey(accessToken)

            if userSuccess and accessSuccess:
                return Response({'userSuccess': True}, status=status.HTTP_200_OK)
            else:
                return Response({'userSuccess': userSuccess, 'accessSuccess': accessSuccess}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        except Exception as e:
            print('레디스 토큰 해제 중 에러 발생:', e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
from meeting_recording_summary.entity.meeting_recording_summary import MeetingRecordingSummary
from meeting_recording_summary.repository.meeting_recording_summary_repository import MeetingRecordingSummaryRepository


class MeetingRecordingSummaryRepositoryImpl(MeetingRecordingSummaryRepository):
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)

        return cls.__instance

    @classmethod
    def getInstance(cls):
        if cls.__instance is None:
            cls.__instance = cls()

        return cls.__instance

    def createSummary(self, username, title, content):
        meetingRecordingSummary = MeetingRecordingSummary.objects.create(title=title, writer=username, content=content)

        return meetingRecordingSummary

    def getPagedSummaryList(self, offset, limit):
        count = MeetingRecordingSummary.objects.count()
        setOffset = count - limit
        if count - limit < 0:
            setOffset = 0
        setLimit = count - offset

        meetingRecordingSummaryList = MeetingRecordingSummary.objects.all().order_by("-regDate")[
            setOffset: setLimit]

        return meetingRecordingSummaryList, count

    def getMeetingRecordingSummaryByMeetingRecordingSummaryId(self, meetingRecordingSummaryId):
        meetingRecordingSummary = MeetingRecordingSummary.objects.get(id=meetingRecordingSummaryId)

        return meetingRecordingSummary

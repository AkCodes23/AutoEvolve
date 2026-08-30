from slotkit import scheduler


class TestFreeSlots:
    """Test the free_slots function."""

    def test_no_meetings(self):
        """With no meetings, the whole day is free."""
        day = (540, 1020)
        meetings = []
        result = scheduler.free_slots(day, meetings)
        assert result == [(540, 1020)]

    def test_single_meeting_in_middle(self):
        """Bug reproduction: afternoon disappears after a midday meeting."""
        day = (540, 1020)
        meetings = [("lunch", (660, 720))]
        result = scheduler.free_slots(day, meetings)
        assert result == [(540, 660), (720, 1020)]

    def test_meeting_at_start(self):
        """Meeting at the start of the day."""
        day = (540, 1020)
        meetings = [("morning", (540, 600))]
        result = scheduler.free_slots(day, meetings)
        assert result == [(600, 1020)]

    def test_meeting_at_end(self):
        """Meeting at the end of the day."""
        day = (540, 1020)
        meetings = [("afternoon", (960, 1020))]
        result = scheduler.free_slots(day, meetings)
        assert result == [(540, 960)]

    def test_multiple_meetings(self):
        """Multiple non-overlapping meetings."""
        day = (540, 1020)
        meetings = [
            ("meeting1", (600, 660)),
            ("meeting2", (720, 780)),
        ]
        result = scheduler.free_slots(day, meetings)
        assert result == [(540, 600), (660, 720), (780, 1020)]

    def test_multiple_meetings_unordered(self):
        """Multiple meetings in non-sorted order."""
        day = (540, 1020)
        meetings = [
            ("meeting2", (720, 780)),
            ("meeting1", (600, 660)),
        ]
        result = scheduler.free_slots(day, meetings)
        assert result == [(540, 600), (660, 720), (780, 1020)]

    def test_consecutive_meetings(self):
        """Back-to-back meetings."""
        day = (540, 1020)
        meetings = [
            ("meeting1", (600, 660)),
            ("meeting2", (660, 720)),
        ]
        result = scheduler.free_slots(day, meetings)
        assert result == [(540, 600), (720, 1020)]

    def test_overlapping_meetings(self):
        """Overlapping meetings (should still handle correctly)."""
        day = (540, 1020)
        meetings = [
            ("meeting1", (600, 700)),
            ("meeting2", (650, 750)),
        ]
        result = scheduler.free_slots(day, meetings)
        assert result == [(540, 600), (750, 1020)]

    def test_meeting_covers_entire_day(self):
        """A meeting that covers the entire working day."""
        day = (540, 1020)
        meetings = [("allday", (540, 1020))]
        result = scheduler.free_slots(day, meetings)
        assert result == []

    def test_single_slot_left(self):
        """Only a single slot remains."""
        day = (540, 1020)
        meetings = [("morning", (540, 1000))]
        result = scheduler.free_slots(day, meetings)
        assert result == [(1000, 1020)]

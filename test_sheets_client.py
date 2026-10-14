from sheets_client import SheetsClient


class FakeWorksheet:
    def __init__(self):
        self.calls = []

    def update_cells(self, cells, value_input_option=None):
        self.calls.append((cells, value_input_option))
        return True


def test_update_statuses_batches_multiple_row_updates_in_one_call():
    client = SheetsClient.__new__(SheetsClient)
    client.header = [
        "Company Name",
        "Name",
        "Email",
        "Status",
        "Sent At",
        "Error Reason",
        "Personalized Summary",
    ]
    client.columns = {
        "company_name": "Company Name",
        "hr_name": "Name",
        "hr_email": "Email",
        "status": "Status",
        "sent_at": "Sent At",
        "error_reason": "Error Reason",
        "personalized_summary": "Personalized Summary",
    }

    worksheet = FakeWorksheet()
    client.worksheet = worksheet

    client.update_statuses([
        {"row_number": 2, "status": "Sent", "sent_at": "2026-09-28 10:00:00"},
        {"row_number": 3, "status": "Not Sent", "error_reason": "Quota exceeded"},
    ])

    assert len(worksheet.calls) == 1
    assert worksheet.calls[0][1] == "RAW"
    assert len(worksheet.calls[0][0]) == 4

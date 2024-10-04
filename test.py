from datetime import datetime, timedelta
class DocumentSubmission:
    def __init__(self, document_name, submitted_date):
        self.document_name = document_name
        self.submitted_date = submitted_date

def calculate_docs_score(submissions):
    current_date = datetime.now()
    total_score = 0
    scoring_criteria = {
        "Before due date": 5,
        "On due date": 4,
        "1 day late": 3,
        "2 days or more late": 2
    }
    for submission in submissions:
        days_diff = (submission.submitted_date - current_date).days
        if days_diff < 0:
            days_after_due = abs(days_diff)
            if days_after_due >= 2:
                score = scoring_criteria["2 days or more late"]
                print(f"{submission.document_name}: Submitted 2 days or more late. Score: {score}")
                total_score += score
            else:
                score = scoring_criteria["1 day late"]
                print(f"{submission.document_name}: Submitted 1 day late. Score: {score}")
                total_score += score
        elif days_diff == 0:
            score = scoring_criteria["On due date"]
            print(f"{submission.document_name}: Submitted on due date. Score: {score}")
            total_score += score
        else:
            score = scoring_criteria["Before due date"]
            print(f"{submission.document_name}: Submitted before due date. Score: {score}")
            total_score += score

    return total_score

def calculate_docs_score_final(total_docs_score):
    return (total_docs_score / 120 * 50 + 50) * 0.30

requirements = [
    "NOA",
    "ICA",
    "ITS",
    "SO/ITC",
    "PR",
    "SD/PR",
    "EF",
    "Interview Form",
    "Exit Survey"
]

due_date = datetime(2024, 9, 30)

submissions = [
    DocumentSubmission("NOA", due_date),
    DocumentSubmission("ICA", due_date),
    DocumentSubmission("ITS", due_date),
    DocumentSubmission("SO/ITC", due_date),
    DocumentSubmission("PR", due_date),
    DocumentSubmission("SD/PR", due_date),
    DocumentSubmission("EF", due_date),
    DocumentSubmission("Interview Form", due_date),
    DocumentSubmission("Exit Survey", due_date),
]

total_docs_score = calculate_docs_score(submissions)
print(f"Total Document Score: {total_docs_score}")

docs_score = calculate_docs_score_final(total_docs_score)
print(f"Final Docs Score: {docs_score:.2f}")

from enum import Enum
import uuid

class RecordType(Enum):
    SDR = "Small Decision Record"
    CDR = "Comprehensive Decision Record"
    IFR = "Implementation Follow-up Record"


class DecisionRecord:
    def __init__(self, record_type: RecordType, data, record_name=None):
        self.record_type = record_type
        if record_name:
            self.id = str(uuid.uuid4()) + record_name + str(record_type)
        else:
            self.id = str(uuid.uuid4()) + str(record_type)
            print("no record name given")
        self.data = data
        self.name = record_name
        self.validate_data()

    def validate_data(self):
        # Validation logic to ensure data conforms to the record type structure
        if self.record_type == RecordType.SDR:
            required_keys = ["previous_record", "summary", "decision", "rationale", "impact", "lessons_learned",
                             "next_record", "review_date"]
        elif self.record_type == RecordType.CDR:
            required_keys = ["previous_record", "context", "decision_drivers", "options_considered", "decision",
                             "consequences", "lessons_learned", "next_record", "implementation_plan",
                             "validation_and_monitoring", "feedback_loop"]
        elif self.record_type == RecordType.IFR:
            required_keys = ["previous_record", "decision_summary", "implementation_steps", "metrics_for_success",
                             "iterations", "lessons_learned", "next_record", "feedback_collection",
                             "pivot_or_persevere"]
        else:
            raise ValueError("Invalid record type")

        # Instead of raising an error for missing keys, fill them with None
        for key in required_keys:
            self.data.setdefault(key, None)

    def to_dict(self):
        return {
            "type": self.record_type,
            "content": self.data
        }

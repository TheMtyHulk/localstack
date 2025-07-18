from enum import StrEnum

from localstack.utils.analytics.metrics import LabeledCounter


class InvocationStatus(StrEnum):
    success = "success"
    error = "error"


# number of EventBridge rule invocations per target (e.g., aws:lambda)
# - status label can be `success` or `error`, see InvocationStatus
# - service label is the target service name
rule_invocation = LabeledCounter(
    namespace="events", name="rule_invocations", labels=["status", "service"]
)

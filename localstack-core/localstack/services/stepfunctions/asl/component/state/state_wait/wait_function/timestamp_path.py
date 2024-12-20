import datetime
import re
from typing import Final

from localstack.aws.api.stepfunctions import ExecutionFailedEventDetails, HistoryEventType
from localstack.services.stepfunctions.asl.component.common.error_name.failure_event import (
    FailureEvent,
    FailureEventException,
)
from localstack.services.stepfunctions.asl.component.common.error_name.states_error_name import (
    StatesErrorName,
)
from localstack.services.stepfunctions.asl.component.common.error_name.states_error_name_type import (
    StatesErrorNameType,
)
from localstack.services.stepfunctions.asl.component.common.variable_sample import VariableSample
from localstack.services.stepfunctions.asl.component.state.state_wait.wait_function.timestamp import (
    TIMESTAMP_FORMAT,
    TIMESTAMP_PATTERN,
)
from localstack.services.stepfunctions.asl.component.state.state_wait.wait_function.wait_function import (
    WaitFunction,
)
from localstack.services.stepfunctions.asl.eval.environment import Environment
from localstack.services.stepfunctions.asl.eval.event.event_detail import EventDetails
from localstack.services.stepfunctions.asl.utils.json_path import extract_json


class TimestampPath(WaitFunction):
    # TimestampPath
    # An absolute time to state_wait until beginning the state specified in the Next field,
    # specified using a path from the state's input data.

    def __init__(self, path: str):
        self.path: Final[str] = path

    def _create_failure_event(self, env: Environment, timestamp_str: str) -> FailureEvent:
        return FailureEvent(
            env=env,
            error_name=StatesErrorName(typ=StatesErrorNameType.StatesRuntime),
            event_type=HistoryEventType.ExecutionFailed,
            event_details=EventDetails(
                executionFailedEventDetails=ExecutionFailedEventDetails(
                    error=StatesErrorNameType.StatesRuntime.to_name(),
                    cause=f"The TimestampPath parameter does not reference a valid ISO-8601 extended offset date-time format string: {self.path} == {timestamp_str}",
                )
            ),
        )

    def _compute_delta_seconds(self, env: Environment, timestamp_str: str):
        try:
            if not re.match(TIMESTAMP_PATTERN, timestamp_str):
                raise FailureEventException(self._create_failure_event(env, timestamp_str))

            # anything lower than seconds is truncated
            processed_timestamp = timestamp_str.rsplit(".", 2)[0]
            # add back the "Z" suffix if we removed it
            if not processed_timestamp.endswith("Z"):
                processed_timestamp = f"{processed_timestamp}Z"
            timestamp = datetime.datetime.strptime(processed_timestamp, TIMESTAMP_FORMAT)
        except Exception:
            raise FailureEventException(self._create_failure_event(env, timestamp_str))

        delta = timestamp - datetime.datetime.now()
        delta_sec = int(delta.total_seconds())
        return delta_sec

    def _get_wait_seconds(self, env: Environment) -> int:
        inp = env.stack[-1]
        timestamp_str: str = extract_json(self.path, inp)
        delta_sec = self._compute_delta_seconds(env=env, timestamp_str=timestamp_str)
        return delta_sec


class TimestampPathVar(TimestampPath):
    variable_sample: Final[VariableSample]

    def __init__(self, variable_sample: VariableSample):
        super().__init__(path=variable_sample.expression)
        self.variable_sample = variable_sample

    def _get_wait_seconds(self, env: Environment) -> int:
        self.variable_sample.eval(env=env)
        timestamp_str = env.stack.pop()
        delta_sec = self._compute_delta_seconds(env=env, timestamp_str=timestamp_str)
        return delta_sec

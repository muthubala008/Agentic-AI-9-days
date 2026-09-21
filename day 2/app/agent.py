import time
from collections.abc import Callable

from app.memory import ConversationStore
from app.providers import AgentError
from app.tools.placement_tools import PlacementTools

MAX_STEPS = 8

SYSTEM = """You are the Placement Assistant for an engineering college's placement cell.
You are talking to the student with roll number {student_id}. Act only for this student.
Use the tools for every fact about drives, eligibility, applications and slots; never guess.
Eligibility is decided by check_eligibility, not by you. Keep replies short and concrete."""


class Agent:
    """A small agent: one student, one conversation, the placement tools."""

    def __init__(
        self,
        provider,
        tools: PlacementTools,
        student_id: str,
        memory: ConversationStore | None = None,
        thread_id: str | None = None,
        on_step: Callable[[dict], None] | None = None,
    ):
        self.provider = provider
        self.tools = tools
        self.system = SYSTEM.format(student_id=student_id)
        self.memory = memory
        self.thread_id = thread_id
        self.on_step = on_step
        self.contents: list[dict] = []  # what the model sees, turn after turn
        self.trace: list[dict] = []  # what happened, step by step

        if self.memory and self.thread_id:
            history = self.memory.load_history(self.thread_id)
            for msg in history:
                self.contents.append({"role": msg["role"], "text": msg["text"]})

    def _log(self, entry: dict) -> None:
        """Add one entry to the trace and tell on_step about it. (Given.)"""
        self.trace.append(entry)
        if self.on_step:
            self.on_step(entry)

    # ------------------------------------------------------------------ Part 2.1

    def run_tool(self, name: str, args: dict) -> dict:
        """Call one tool with self.tools.call(name, args). Never raise."""
        try:
            return self.tools.call(name, args)
        except NotImplementedError as e:
            return {
                "error": "not_implemented",
                "hint": f"The tool '{name}' is not implemented yet: {e}",
            }
        except Exception as e:
            return {
                "error": "tool_failed",
                "hint": f"Execution of tool '{name}' failed: {e}",
            }

    # ------------------------------------------------------------------ Part 2.2

    def ask(self, text: str) -> str:
        """One user turn: loop model calls and tool calls until the model answers."""
        step_counter = 0

        # Memory persistence for incoming user message
        if self.memory and self.thread_id:
            self.memory.append_message(self.thread_id, "user", text)
            run_id = self.memory.start_run(self.thread_id, self.provider.model)
        else:
            run_id = None

        self.contents.append({"role": "user", "text": text})

        try:
            while step_counter < MAX_STEPS:
                step_counter += 1

                # Step 1: Model generation
                tools_schema = list(self.tools.functions().values())
                turn = self.provider.generate(self.system, self.contents, tools_schema)

                # Record model step in memory and trace
                if self.memory and run_id:
                    self.memory.record_model_step(
                        run_id=run_id,
                        seq=step_counter,
                        tokens_in=turn.tokens_in,
                        tokens_out=turn.tokens_out,
                    )

                self._log({
                    "step": step_counter,
                    "kind": "model",
                    "tokens_in": turn.tokens_in,
                    "tokens_out": turn.tokens_out,
                })

                # Step 2: Handle completion (No tool calls)
                if not turn.tool_calls:
                    reply = turn.text
                    self.contents.append({
                        "role": "model",
                        "text": reply,
                        "raw": turn.raw,
                    })

                    if self.memory and self.thread_id and run_id:
                        self.memory.append_message(self.thread_id, "model", reply)
                        self.memory.finish_run(run_id, "succeeded")

                    return reply

                # Step 3: Handle tool calls
                self.contents.append({
                    "role": "model",
                    "text": turn.text,
                    "raw": turn.raw,
                    "tool_calls": turn.tool_calls,
                })

                for tc in turn.tool_calls:
                    step_counter += 1
                    if step_counter > MAX_STEPS:
                        raise AgentError("step_limit", "Exceeded maximum allowed steps")

                    name = tc.name
                    args = tc.args

                    start_time = time.perf_counter()
                    res = self.run_tool(name, args)
                    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                    ok = "error" not in res

                    if self.memory and run_id:
                        self.memory.record_tool_call(
                            run_id=run_id,
                            seq=step_counter,
                            name=name,
                            args=args,
                            result=res,
                            ok=ok,
                            latency_ms=elapsed_ms,
                        )

                    self._log({
                        "step": step_counter,
                        "kind": "tool",
                        "tool": name,
                        "args": args,
                        "result": res,
                        "ok": ok,
                        "ms": elapsed_ms,
                    })

                    self.contents.append({
                        "role": "tool",
                        "name": name,
                        "result": res,
                    })

            raise AgentError("step_limit", "Exceeded maximum allowed steps without reaching an answer")

        except AgentError as e:
            if self.memory and run_id:
                self.memory.finish_run(run_id, "failed", error_code=e.code)
            raise
class LoomError(Exception):
    code = "LOOM_ERROR"

    def details(self) -> dict:
        """传输层附加到错误体的结构化字段（默认无）。子类覆盖以让错误可行动化。"""
        return {}


class ValidationFailed(LoomError):
    code = "VALIDATION_ERROR"  # 结构不合规，拒绝写入


class Conflict(LoomError):
    code = "CONFLICT"  # OCC hash 不一致 / 重名

    def __init__(
        self,
        message: str,
        current_hash: str | None = None,
        changed_sections: list[str] | None = None,
    ):
        super().__init__(message)
        self.current_hash = current_hash  # 当前磁盘 hash：agent 可据此一步重试，免去再读
        self.changed_sections = changed_sections  # 你读后到现在内容有差异的节标题

    def details(self) -> dict:
        d: dict = {}
        if self.current_hash is not None:
            d["current_hash"] = self.current_hash
        if self.changed_sections is not None:
            d["changed_sections"] = self.changed_sections
        return d


class NotFound(LoomError):
    code = "NOT_FOUND"


class LockTimeout(LoomError):
    code = "LOCK_TIMEOUT"

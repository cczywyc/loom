class LoomError(Exception):
    code = "LOOM_ERROR"


class ValidationFailed(LoomError):
    code = "VALIDATION_ERROR"  # 结构不合规，拒绝写入


class Conflict(LoomError):
    code = "CONFLICT"  # OCC hash 不一致 / 重名


class NotFound(LoomError):
    code = "NOT_FOUND"


class LockTimeout(LoomError):
    code = "LOCK_TIMEOUT"

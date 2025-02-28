class BaseLogger:
    def __init__(self) -> None:
        # Khởi tạo một logger nếu cần
        pass

    def info(self, message: str) -> None:
        print(f"[INFO] {message}")  # In thông tin ra console

    def error(self, message: str) -> None:
        print(f"[ERROR] {message}")  # In lỗi ra console

"""
Chương trình chính khởi động ứng dụng Quản lý Đại lý Bảo hiểm.
"""

from controller.controller import AgencyController

if __name__ == "__main__":
    app = AgencyController()
    app.run()

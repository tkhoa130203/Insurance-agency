"""
Module hiển thị giao diện và nhận đầu vào từ người dùng.
"""

class AgencyView:
    def display_menu(self):
        print("\n📋 MENU:")
        print("1. Thêm đại lý")
        print("2. Xem danh sách đại lý")
        print("3. Tìm đại lý theo tên")
        print("4. Thoát")

    def get_input_agency(self):
        name = input("Tên đại lý: ")
        region = input("Khu vực: ")
        manager = input("Tên người quản lý: ")
        return name, region, manager

    def get_search_keyword(self):
        return input("Nhập tên cần tìm: ")

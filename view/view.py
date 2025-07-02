"""
Hiển thị menu và giao diện người dùng.
"""
class AgencyView:
    def display_menu(self):
        print("1. Thêm đại lý")
        print("2. Hiển thị danh sách đại lý")
        print("3. Tìm kiếm đại lý theo tên")
        print("4. Thoát")

    def get_input_agency(self):
        name = input("Nhập tên đại lý: ")
        region = input("Nhập khu vực: ")
        manager = input("Nhập tên quản lý: ")
        return name, region, manager

    def show_agencies(self, agencies):
        if not agencies:
            print("Không có đại lý nào.")
        else:
            for agency in agencies:
                print(agency)

    def get_search_keyword(self):
        return input("Nhập từ khóa tìm kiếm: ")
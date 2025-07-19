"""
Module điều khiển luồng giữa model và view.
"""

from model.model import AgencyDatabase

class AgencyController:
    def __init__(self):
        # Tạo model để quản lý dữ liệu của đại lý
        self.model = AgencyDatabase()

    
        while True:
            # Menu lựa chọn
            self.view.display_menu()
            choice = input("Chọn chức năng (1-4): ").strip()

            if choice == '1':
                 # Thêm đại lý mới
                name, region, manager = self.view.get_input_agency()
                self.model.bring_on_new_agency(name, region, manager)
            elif choice == '2':
                # Danh sách đại lý
                self.model.show_me_all_the_agencies()
            elif choice == '3':
                # Tìm kiếm đại lý 
                keyword = self.view.get_search_keyword()
                self.model.find_agencies_by_name(keyword)
            elif choice == '4':
                # Thoát
                print("👋 Tạm biệt!")
                break
            else:
                # Báo lỗi
                print("⚠️ Lựa chọn không hợp lệ.")

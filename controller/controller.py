"""
Xử lý logic giữa model và view.
"""

from model.model import AgencyModel
from view.view import AgencyView

class AgencyController:
    def __init__(self):
        self.model = AgencyModel()
        self.view = AgencyView()

    def run(self):
        while True:
            self.view.display_menu()
            choice = input("👉 Nhập lựa chọn của bạn: ")

            if choice == '1':
                name, region, manager = self.view.get_input_agency()
                self.model.add_agency(name, region, manager)
                print("✅ Đại lý đã được thêm thành công!")

            elif choice == '2':
                agencies = self.model.get_all_agencies()
                self.view.show_agencies(agencies)

            elif choice == '3':
                keyword = self.view.get_search_keyword()
                results = self.model.search_agency_by_name(keyword)
                self.view.show_agencies(results)

            elif choice == '4':
                print("👋 Cảm ơn bạn! Hẹn gặp lại.")
                break

            else:
                print("⚠️ Lựa chọn không hợp lệ! Vui lòng thử lại.")

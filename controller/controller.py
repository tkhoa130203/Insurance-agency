"""
Module điều khiển luồng giữa model và view.
"""

from model.model import AgencyDatabase
from view.view import AgencyView

class AgencyController:
    def __init__(self):
        self.model = AgencyDatabase()
        self.view = AgencyView()

    def run(self):
        while True:
            self.view.display_menu()
            choice = input("Chọn chức năng (1-4): ").strip()

            if choice == '1':
                name, region, manager = self.view.get_input_agency()
                self.model.bring_on_new_agency(name, region, manager)
            elif choice == '2':
                self.model.show_me_all_the_agencies()
            elif choice == '3':
                keyword = self.view.get_search_keyword()
                self.model.find_agencies_by_name(keyword)
            elif choice == '4':
                print("👋 Tạm biệt!")
                break
            else:
                print("⚠️ Lựa chọn không hợp lệ.")

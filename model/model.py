"""
Định nghĩa dữ liệu và logic đại lý.
"""

class Agency:
    def __init__(self, name, region, manager):
        self.name = name
        self.region = region
        self.manager = manager

    def __str__(self):
        return f"{self.name} - Khu vực: {self.region}, Quản lý: {self.manager}"


class AgencyModel:
    def __init__(self):
        self.agencies = []

    def add_agency(self, name, region, manager):
        agency = Agency(name, region, manager)
        self.agencies.append(agency)

    def get_all_agencies(self):
        return self.agencies

    def search_agency_by_name(self, keyword):
        return [a for a in self.agencies if keyword.lower() in a.name.lower()]

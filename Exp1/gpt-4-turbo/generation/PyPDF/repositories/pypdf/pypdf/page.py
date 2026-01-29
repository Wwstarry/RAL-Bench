class PageObject:
    def __init__(self, pdf, page_dict, index=None):
        self.pdf = pdf
        self.page_dict = page_dict
        self.index = index
        self._rotation = None

    def rotate(self, angle):
        # Rotates the page by the given angle (degrees)
        current = self.page_dict.get("/Rotate", 0)
        new_angle = (current + angle) % 360
        self.page_dict["/Rotate"] = new_angle
        self._rotation = new_angle

    @property
    def rotation(self):
        if self._rotation is not None:
            return self._rotation
        return self.page_dict.get("/Rotate", 0)

    @property
    def media_box(self):
        mb = self.page_dict.get("/MediaBox")
        if mb:
            return [float(x) for x in mb]
        return [0, 0, 612, 792]  # Default A4

    def get_contents(self):
        return self.page_dict.get("/Contents")

    def __getitem__(self, key):
        return self.page_dict[key]

    def __setitem__(self, key, value):
        self.page_dict[key] = value

    def __repr__(self):
        return f"<PageObject index={self.index}>"
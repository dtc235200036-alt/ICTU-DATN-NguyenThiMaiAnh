from enum import StrEnum


class VaiTro(StrEnum):
    SINH_VIEN = "SINH_VIEN"
    GIANG_VIEN = "GIANG_VIEN"
    BO_MON = "BO_MON"


ANY_ROLE = (VaiTro.SINH_VIEN, VaiTro.GIANG_VIEN, VaiTro.BO_MON)

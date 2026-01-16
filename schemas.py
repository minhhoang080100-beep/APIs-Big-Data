"""
API Request/Response schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class LoginRequest(BaseModel):
    """Login request schema"""
    Username: str = Field(..., description="Username")
    Password: str = Field(..., description="Password (can be plain or hashed)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "Username": "abc",
                    "Password": "6504E4EF9274BDE48162B6F2BE0FDF0"
                }
            ]
        }
    }


class LoginResponse(BaseModel):
    """Login response schema"""
    AccessToken: str = Field(..., description="JWT access token")
    Code: str = Field(..., description="Response code (1 = success)")
    Message: str = Field(..., description="Response message")
    ExpireIn: str = Field(..., description="Token expiration time (e.g., '8h')")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "AccessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "Code": "1",
                    "Message": "Login thành công",
                    "ExpireIn": "8h"
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Error response schema"""
    Code: str = Field(..., description="Error code")
    Message: str = Field(..., description="Error message")


# Customer API Schemas

class CustomerMetadata(BaseModel):
    """Customer metadata"""
    isDeleted: int = Field(0, description="0 = chưa xóa, 1 = đã xóa")
    modifiedDate: Optional[str] = Field(None, description="Thời gian sửa đổi gần nhất")


class CustomerData(BaseModel):
    """Customer data model"""
    reportDate: str = Field(..., description="Ngày báo cáo")
    customerCode: str = Field(..., description="Mã khách hàng")  # Changed from int to str
    customerNameVN: str = Field("", description="Tên khách hàng (VN)")
    customerNameEN: str = Field("", description="Tên khách hàng (EN)")
    customerTaxCode: str = Field("", description="Mã số thuế/ID quốc tế")
    customerPhoneNum: str = Field("", description="Số điện thoại")
    customerAddress: str = Field("", description="Địa chỉ")
    customerEmail: str = Field("", description="Email")
    isCarrier: int = Field(0, description="1 = hãng tàu, 0 = không phải")
    isAgent: int = Field(0, description="1 = đại lý, 0 = không phải")
    customerStatus: str = Field("", description="Trạng thái khách hàng")
    metadata: CustomerMetadata

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reportDate": "2025-10-05",
                    "customerCode": 6001,
                    "customerNameVN": "Công Ty TNHH ABC",
                    "customerNameEN": "Company ABC",
                    "customerTaxCode": "0101234567",
                    "customerPhoneNum": "0904123456",
                    "customerAddress": "Cảng Nghệ Tĩnh",
                    "customerEmail": "contact@abc.com",
                    "isCarrier": 1,
                    "isAgent": 0,
                    "customerStatus": "",
                    "metadata": {
                        "isDeleted": 0,
                        "modifiedDate": "2025-09-15T10:30:00"
                    }
                }
            ]
        }
    }


class CustomerListResponse(BaseModel):
    """Response for customer list"""
    code: str = Field("1", description="Mã trả về (1 = thành công)")
    message: str = Field("", description="Thông báo")
    data: List[CustomerData] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "1",
                    "message": "Lấy dữ liệu thành công",
                    "data": [
                        # CustomerData example here
                    ]
                }
            ]
        }
    }


class CustomerSingleResponse(BaseModel):
    """Response for single customer"""
    code: str = Field("1", description="Mã trả về")
    message: str = Field("", description="Thông báo")
    data: Optional[CustomerData] = None


# Cargo Category API Schemas

class CargoData(BaseModel):
    """Cargo category data model"""
    reportDate: str = Field(..., description="Ngày lấy dữ liệu")
    cargoId: int = Field(..., description="Mã độc nhất định danh nhóm hàng hóa")
    cargoParentId: int = Field(..., description="Mã nhóm hàng cha")
    cargoTypeId: int = Field(..., description="Mã loại hàng (cargo type: Hàng container, Hàng RORO, Hàng bách hóa, Hàng xá, Hàng khí hóa lỏng)")
    cargoName: str = Field("", description="Tên nhóm hàng hóa")
    createdDate: Optional[str] = Field(None, description="Ngày tạo bản ghi")
    modifiedDate: Optional[str] = Field(None, description="Ngày sửa bản ghi")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reportDate": "2025-10-05",
                    "cargoId": 1234,
                    "cargoParentId": 123,
                    "cargoTypeId": 12345,
                    "cargoName": "Hàng sắt thép",
                    "createdDate": "2023-01-01T00:00:00Z",
                    "modifiedDate": "2023-01-01T00:00:00Z"
                }
            ]
        }
    }


class CargoListResponse(BaseModel):
    """Response for cargo category list"""
    code: str = Field("1", description="Mã trả về (1 = thành công)")
    message: str = Field("", description="Thông báo")
    data: List[CargoData] = Field(default_factory=list)


class CargoSingleResponse(BaseModel):
    """Response for single cargo category"""
    code: str = Field("1", description="Mã trả về")
    message: str = Field("", description="Thông báo")
    data: Optional[CargoData] = None


# Cargo Type API Schemas

class CargoTypeData(BaseModel):
    """Cargo type data model"""
    reportDate: str = Field(..., description="Ngày lấy dữ liệu")
    cargoTypeId: str = Field(..., description="Id loại hàng")
    cargoTypeName: str = Field("", description="Tên loại hàng (Hàng container, Hàng RORO, Hàng bách hóa, Hàng xá, Hàng khí hóa lỏng (LNG))")
    createdDate: Optional[str] = Field(None, description="Ngày tạo bản ghi")
    modifiedDate: Optional[str] = Field(None, description="Ngày sửa bản ghi")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reportDate": "2025-10-05",
                    "cargoTypeId": "CRGTYPE1",
                    "cargoTypeName": "Hàng container",
                    "createdDate": "2023-01-01T00:00:00Z",
                    "modifiedDate": "2023-01-01T00:00:00Z"
                }
            ]
        }
    }


class CargoTypeListResponse(BaseModel):
    """Response for cargo type list"""
    code: str = Field("1", description="Mã trả về (1 = thành công)")
    message: str = Field("", description="Thông báo")
    data: List[CargoTypeData] = Field(default_factory=list)


class CargoTypeSingleResponse(BaseModel):
    """Response for single cargo type"""
    code: str = Field("1", description="Mã trả về")
    message: str = Field("", description="Thông báo")
    data: Optional[CargoTypeData] = None


# Handling Method API Schemas

class HandlingMethodData(BaseModel):
    """Handling method data model"""
    reportDate: str = Field(..., description="Ngày lấy dữ liệu")
    handlingMethodId: str = Field(..., description="Mã phương án tác nghiệp")
    handlingMethodName: str = Field("", description="Tên phương án tác nghiệp: Nhập hàng từ tàu lên kho bãi, Xuất hàng từ kho bãi xuống tàu...")
    createdDate: Optional[str] = Field(None, description="Ngày tạo bản ghi")
    modifiedDate: Optional[str] = Field(None, description="Ngày sửa bản ghi")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reportDate": "2025-10-05",
                    "handlingMethodId": "NTAU",
                    "handlingMethodName": "Nhập hàng từ tàu lên kho bãi",
                    "createdDate": "2023-01-01T00:00:00Z",
                    "modifiedDate": "2023-01-01T00:00:00Z"
                }
            ]
        }
    }


class HandlingMethodListResponse(BaseModel):
    """Response for handling method list"""
    code: str = Field("1", description="Mã trả về (1 = thành công)")
    message: str = Field("", description="Thông báo")
    data: List[HandlingMethodData] = Field(default_factory=list)


class HandlingMethodSingleResponse(BaseModel):
    """Response for single handling method"""
    code: str = Field("1", description="Mã trả về")
    message: str = Field("", description="Thông báo")
    data: Optional[HandlingMethodData] = None


# ============================================================
# Class (Cargo Direction / Hướng Tàu) Schemas
# ============================================================

class ClassData(BaseModel):
    """Schema for Class (Cargo Direction) data"""
    reportDate: str
    classId: str
    className: str
    createdDate: Optional[str] = None
    modifiedDate: Optional[str] = None
    

class ClassListResponse(BaseModel):
    """Response for Class list endpoint"""
    code: str
    message: str
    data: List[ClassData]

class ClassSingleResponse(BaseModel):
    """Response for single Class endpoint"""
    code: str
    message: str
    data: ClassData


# ============================================================
# Ship Details Schemas
# ============================================================

class ShipData(BaseModel):
    """Schema for Ship Details data"""
    reportDate: str = Field(..., description="Ngày lấy dữ liệu")
    shipId: str = Field(..., description="Mã tàu")
    shipIMO: str = Field(..., description="Mã hàng hải quốc tế IMO")
    shipFullName: str = Field("", description="Tên tàu đầy đủ")
    shipGroup: str = Field("", description="Phân loại tàu theo nhóm")
    flagState: str = Field("", description="Cờ tàu")
    shipLOA: Optional[str] = Field(None, description="Chiều dài tàu (Length Overall)")
    shipBeam: Optional[str] = Field(None, description="Chiều rộng tàu (Maximum Breadth)")
    shipGRT: Optional[str] = Field(None, description="Tổng dung tích tàu (Gross Register Tonnage)")
    shipType: Optional[str] = Field(None, description="Loại tàu")
    shipDWT: Optional[str] = Field(None, description="Trọng tải toàn phần")
    shipOwner: Optional[str] = Field(None, description="Tên đơn vị sở hữu tàu")
    createdDate: Optional[str] = Field(None, description="Ngày tạo bản ghi")
    modifiedDate: Optional[str] = Field(None, description="Ngày sửa bản ghi")


class ShipListResponse(BaseModel):
    """Response for ship list endpoint"""
    code: str = Field("1", description="Mã trả về (1 = thành công)")
    message: str = Field("", description="Thông báo")
    data: List[ShipData] = Field(default_factory=list)


class ShipSingleResponse(BaseModel):
    """Response for single ship endpoint"""
    code: str = Field("1", description="Mã trả về")
    message: str = Field("", description="Thông báo")
    data: Optional[ShipData] = None


# ============================================================
# Bulk Gate Volumes (Hàng Rời qua Cổng Cảng/Kho Bãi) Schemas
# ============================================================

class BulkGateVolumeData(BaseModel):
    """Schema for Bulk Gate Volume data"""
    reportDate: str = Field(..., description="Ngày lấy dữ liệu")
    finishDate: str = Field(..., description="Ngày nhận sản lượng")
    companyId: str = Field(..., description="Mã đơn vị cảng biển")
    cargoTypeId: str = Field(..., description="Loại hàng hóa (hàng container, hàng rời, hàng RORO...)")
    cargoCategoryId: str = Field(..., description="Nhóm hàng hóa")
    handlingMethodId: str = Field(..., description="Phương án tác nghiệp")
    bulkOriginId: str = Field(..., description="Nguồn gốc hàng hóa")
    bulkWeight: float = Field(..., description="Tổng trọng lượng (đơn vị: tấn)")
    customerCode: str = Field(..., description="Mã khách hàng")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reportDate": "2025-10-15",
                    "finishDate": "2025-10-15",
                    "companyId": "101",
                    "cargoTypeId": "1234",
                    "cargoCategoryId": "1234",
                    "handlingMethodId": "XBAI",
                    "bulkOriginId": "1234",
                    "bulkWeight": 5000.0,
                    "customerCode": "CSTM1234"
                }
            ]
        }
    }


class BulkGateVolumeListResponse(BaseModel):
    """Response for bulk gate volume list endpoint"""
    code: str = Field("1", description="Mã trả về (1 = thành công)")
    message: str = Field("", description="Thông báo")
    data: List[BulkGateVolumeData] = Field(default_factory=list)


# ============================================================
# Bulk Quay Volumes (Hàng Rời tại Cầu Tàu/Bến) Schemas
# ============================================================

class BulkQuayVolumeData(BaseModel):
    """Schema for Bulk Quay Volume data"""
    reportDate: str = Field(..., description="Ngày lấy dữ liệu")
    finishDate: str = Field(..., description="Ngày ghi nhận sản lượng")
    companyId: str = Field(..., description="Mã đơn vị cảng biển")
    shipId: str = Field(..., description="Mã tàu vận chuyển hàng rời")
    shipAgentId: str = Field(..., description="Mã đại lý tàu")
    cargoTypeId: str = Field(..., description="Mã loại hàng hóa")
    cargoCategoryId: str = Field(..., description="Mã nhóm hàng hóa")
    handlingMethodId: str = Field(..., description="Phương án tác nghiệp")
    shipClassId: str = Field(..., description="Hướng tàu")
    bulkOriginId: str = Field(..., description="Nguồn gốc hàng hóa")
    bulkWeight: float = Field(..., description="Tổng trọng lượng hàng (tấn)")


class BulkQuayVolumeListResponse(BaseModel):
    """Response for bulk quay volume list endpoint"""
    code: str = Field("1", description="Mã trả về (1 = thành công)")
    message: str = Field("", description="Thông báo")
    data: List[BulkQuayVolumeData] = Field(default_factory=list)


# ============================================================
# Container Quay Volumes (Container tại Cầu Tàu/Bến) Schemas
# ============================================================

class ContainerQuayVolumeData(BaseModel):
    """Schema for Container Quay Volume data"""
    reportDate: str = Field(..., description="Ngày lấy dữ liệu")
    companyId: str = Field(..., description="Mã đơn vị cảng biển")
    shipId: str = Field(..., description="Mã danh sách tàu chở container")
    classId: str = Field(..., description="Hướng tàu (nhập, xuất)")
    originId: str = Field(..., description="Nguồn gốc hàng hóa (xuất địa, Nhập)")
    containerWeight: float = Field(..., description="Tổng trọng lượng container (Tấn)")
    containerTEU: int = Field(..., description="Tổng TEU qua đư thông qua cảng")
    handlingMethodId: str = Field(..., description="Phương án tác nghiệp")
    finishDate: str = Field(..., description="Ngày ghi nhận sản lượng")
    shipOperatorId: str = Field(..., description="Chủ khai thác của tàu")
    containerOperatorId: str = Field(..., description="Chủ khai thác vận container")


class ContainerQuayVolumeListResponse(BaseModel):
    """Response for container quay volume list endpoint"""
    code: str = Field("1", description="Mã trả về (1 = thành công)")
    message: str = Field("", description="Thông báo")
    data: List[ContainerQuayVolumeData] = Field(default_factory=list)

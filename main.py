"""
FastAPI Application - TOS Big Data API Server
"""
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta, datetime
from typing import Optional
import logging

from schemas import (
    LoginRequest, 
    LoginResponse, 
    ErrorResponse,
    CustomerListResponse,
    CustomerSingleResponse,
    CustomerData,
    CustomerMetadata,
    CargoListResponse,
    CargoSingleResponse,
    CargoData,
    CargoTypeListResponse,
    CargoTypeSingleResponse,
    CargoTypeData,
    HandlingMethodListResponse,
    HandlingMethodSingleResponse,
    HandlingMethodData,
    ClassListResponse,
    ClassSingleResponse,
    ClassData,
    ShipListResponse,
    ShipSingleResponse,
    ShipData,
    BulkGateVolumeListResponse,
    BulkGateVolumeData,
    BulkQuayVolumeListResponse,
    BulkQuayVolumeData,
    ContainerQuayVolumeListResponse,
    ContainerQuayVolumeData
)
from database import db
from auth import (
    authenticate_user, 
    create_access_token, 
    verify_token,
    ACCESS_TOKEN_EXPIRE_HOURS
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TOS Big Data API",
    description="API Server for Terminal Operating System Big Data Integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security
security = HTTPBearer()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TOS Big Data API Server",
        "version": "1.0.0",
        "endpoints": {
            "login": "/api/login",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.post(
    "/api/login",
    response_model=LoginResponse,
    responses={
        200: {
            "description": "Login successful",
            "model": LoginResponse
        },
        401: {
            "description": "Login failed",
            "model": ErrorResponse
        }
    },
    summary="User Login",
    tags=["Authentication"]
)
async def login(request: LoginRequest):
    """
    Login endpoint to get access token
    
    - **Username**: User's username
    - **Password**: User's password (can be plain or pre-hashed)
    
    Returns:
    - **AccessToken**: JWT token for API authentication
    - **Code**: Response code (1 = success)
    - **Message**: Response message
    - **ExpireIn**: Token expiration time
    """
    logger.info(f"Login attempt for user: {request.Username}")
    
    # Authenticate user
    user = authenticate_user(request.Username, request.Password)
    
    if not user:
        logger.warning(f"Login failed for user: {request.Username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "Code": "0",
                "Message": "Tên đăng nhập hoặc mật khẩu không đúng"
            }
        )
    
    # Create access token
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    logger.info(f"Login successful for user: {request.Username}")
    
    return LoginResponse(
        AccessToken=access_token,
        Code="1",
        Message="Login thành công",
        ExpireIn=f"{ACCESS_TOKEN_EXPIRE_HOURS}h"
    )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get current authenticated user from token
    """
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


@app.get(
    "/api/protected",
    tags=["Testing"]
)
async def protected_route(current_user = Depends(get_current_user)):
    """
    Protected route example (for testing authentication)
    """
    return {
        "message": "This is a protected route",
        "user": current_user.username,
        "token_expires": current_user.exp.isoformat() if current_user.exp else None
    }


# Customer API Endpoints

@app.get(
    "/api/customers",
    response_model=CustomerListResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        401: {"description": "Chưa xác thực"},
        500: {"description": "Lỗi server"}
    },
    summary="Lấy danh sách khách hàng",
    tags=["Customers"]
)
async def get_customers(
    startDate: Optional[str] = Query(None, description="Lọc theo ngày tạo (from)"),
    endDate: Optional[str] = Query(None, description="Lọc theo ngày tạo (to)"),
    customerTaxCode: Optional[str] = Query(None, description="Lọc theo mã số thuế"),
    companyId: Optional[str] = Query(None, description="Mã công ty"),
    customerType: Optional[str] = Query(None, description="Loại khách hàng"),
    current_user = Depends(get_current_user)
):
    """
    Lấy danh sách khách hàng với các bộ lọc tùy chọn
    
    - **startDate**: Lọc theo ngày tạo (YYYY-MM-DD)
    - **endDate**: Lọc theo ngày tạo (YYYY-MM-DD)
    - **customerTaxCode**: Mã số thuế
    - **companyId**: Mã công ty
    - **customerType**: Loại khách hàng
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Customer list request by {current_user.username}")
    
    try:
        # Build SQL query with correct column names from actual schema
        query = """
            SELECT 
                partnerGuid,
                partnerCode,
                partnerShortName,
                partnerFullName,
                partnerFullNameEN,
                partnerTaxCode,
                partnerBankName,
                partnerBankNumber,
                partnerFax,
                partnerEmail,
                partnerTel,
                partnerWebsite,
                partnerAddress,
                partnerDirector,
                isCashPayment,
                cargoGroupListId,
                rowInvisible,
                rowDeleted,
                [guid],
                createUserId,
                updateUserId,
                createTime,
                updateTime,
                fontColor,
                apiCode,
                partnerMemberListEmail,
                partnerMemberListMobile,
                buyerFullName,
                buyerIDNumber,
                partnerBudgetCode
            FROM dbo.Partner
            WHERE 1=1
        """
        
        params = []
        
        # Apply filters
        if startDate:
            query += " AND CAST(updateTime AS DATE) >= ?"
            params.append(startDate)
        
        if endDate:
            query += " AND CAST(updateTime AS DATE) <= ?"
            params.append(endDate)
        
        if customerTaxCode:
            query += " AND partnerTaxCode = ?"
            params.append(customerTaxCode)
        
        # Filter out deleted records (only get rowDeleted = 0)
        query += " AND rowDeleted = 0"
        
        # Add ordering
        query += " ORDER BY partnerCode"
        
        # Execute query
        results = db.execute_query(query, tuple(params) if params else None)
        
        # Transform to CustomerData format
        customers = []
        for row in results:
            customer = CustomerData(
                reportDate=datetime.now().strftime("%Y-%m-%d"),
                customerCode=str(row.get('partnerCode', '')),  # Convert to string
                customerNameVN=row.get('partnerFullName', '') or row.get('partnerShortName', '') or '',
                customerNameEN=row.get('partnerFullNameEN', '') or '',
                customerTaxCode=row.get('partnerTaxCode', '') or '',
                customerPhoneNum=row.get('partnerTel', '') or '',
                customerAddress=row.get('partnerAddress', '') or '',
                customerEmail=row.get('partnerEmail', '') or '',
                isCarrier=0,
                isAgent=0,
                customerStatus='',
                metadata=CustomerMetadata(
                    isDeleted=row.get('rowDeleted', 0) or 0,
                    modifiedDate=row.get('updateTime', None)
                )
            )
            customers.append(customer)
        
        logger.info(f"Returned {len(customers)} customers")
        
        return CustomerListResponse(
            code="1",
            message="Lấy dữ liệu thành công" if customers else "Không có dữ liệu",
            data=customers
        )
        
    except Exception as e:
        logger.error(f"Error fetching customers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


@app.get(
    "/api/customers/{customer_id}",
    response_model=CustomerSingleResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        404: {"description": "Không tìm thấy khách hàng"},
        401: {"description": "Chưa xác thực"}
    },
    summary="Lấy thông tin khách hàng theo ID",
    tags=["Customers"]
)
async def get_customer_by_id(
    customer_id: str,
    companyId: Optional[str] = Query(None, description="Mã công ty"),
    current_user = Depends(get_current_user)
):
    """
    Lấy thông tin chi tiết của một khách hàng
    
    - **customer_id**: Mã khách hàng
    - **companyId**: Mã công ty (optional)
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Customer detail request for ID {customer_id} by {current_user.username}")
    
    try:
        query = """
            SELECT 
                partnerGuid,
                partnerCode,
                partnerShortName,
                partnerFullName,
                partnerFullNameEN,
                partnerTaxCode,
                partnerBankName,
                partnerBankNumber,
                partnerFax,
                partnerEmail,
                partnerTel,
                partnerWebsite,
                partnerAddress,
                partnerDirector,
                isCashPayment,
                cargoGroupListId,
                rowInvisible,
                rowDeleted,
                updateTime
            FROM dbo.Partner
            WHERE partnerCode = ?
            AND rowDeleted = 0
        """
        
        results = db.execute_query(query, (customer_id,))
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "0",
                    "message": "Không tìm thấy khách hàng"
                }
            )
        
        row = results[0]
        customer = CustomerData(
            reportDate=datetime.now().strftime("%Y-%m-%d"),
            customerCode=str(row.get('partnerCode', '')),  # Convert to string
            customerNameVN=row.get('partnerFullName', '') or row.get('partnerShortName', '') or '',
            customerNameEN=row.get('partnerFullNameEN', '') or '',
            customerTaxCode=row.get('partnerTaxCode', '') or '',
            customerPhoneNum=row.get('partnerTel', '') or '',
            customerAddress=row.get('partnerAddress', '') or '',
            customerEmail=row.get('partnerEmail', '') or '',
            isCarrier=0,
            isAgent=0,
            customerStatus='',
            metadata=CustomerMetadata(
                isDeleted=row.get('rowDeleted', 0) or 0,
                modifiedDate=row.get('updateTime', None)
            )
        )
        
        logger.info(f"Customer {customer_id} found")
        
        return CustomerSingleResponse(
            code="1",
            message="Lấy dữ liệu thành công",
            data=customer
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


# Cargo Category API Endpoints

@app.get(
    "/api/cargoCategory",
    response_model=CargoListResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        401: {"description": "Chưa xác thực"},
        500: {"description": "Lỗi server"}
    },
    summary="Lấy danh sách nhóm hàng hóa",
    tags=["Cargo Category"]
)
async def get_cargo_categories(
    cargoTypeId: Optional[int] = Query(None, description="Lọc theo loại hàng"),
    page: Optional[int] = Query(1, description="Trang hiện tại (pagination)", ge=1),
    limit: Optional[int] = Query(50, description="Số lượng records mỗi trang", ge=1, le=100),
    companyId: Optional[str] = Query(None, description="Mã công ty"),
    current_user = Depends(get_current_user)
):
    """
    Lấy danh sách các nhóm hàng hóa với phân trang và bộ lọc
    
    - **cargoTypeId**: Lọc theo loại hàng
    - **page**: Trang hiện tại (default: 1)
    - **limit**: Số records mỗi trang (default: 50, max: 100)
    - **companyId**: Mã công ty (optional)
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Cargo category list request by {current_user.username}")
    
    try:
        # Build base query
        query = """
            SELECT 
                cargoId,
                cargoCode,
                cargoName,
                cargoGroupId,
                cargoGroupBillingId,
                customsHsCodeId,
                rowInvisible,
                rowDeleted,
                createUserId,
                updateUserId,
                createTime,
                updateTime,
                cargoGroupCode,
                cargoGroupName,
                cargoGroupDescription,
                cargoGroupBillingCode,
                cargoGroupBillingName,
                cargoGroupBillingDescription
            FROM dbo.vwCargo
            WHERE 1=1
        """
        
        params = []
        
        # Apply filters
        if cargoTypeId:
            query += " AND cargoGroupId = ?"
            params.append(cargoTypeId)
        
        # Filter out deleted records (only get rowDeleted = 0)
        query += " AND rowDeleted = 0"
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Add ordering and pagination
        query += " ORDER BY cargoId OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])
        
        # Execute query
        results = db.execute_query(query, tuple(params) if params else None)
        
        # Transform to CargoData format
        cargos = []
        for row in results:
            cargo = CargoData(
                reportDate=datetime.now().strftime("%Y-%m-%d"),
                cargoId=row.get('cargoId', 0),
                cargoParentId=0,  # Not available in view, set to 0
                cargoTypeId=row.get('cargoGroupId', 0) or 0,
                cargoName=row.get('cargoName', '') or row.get('cargoGroupName', '') or '',
                createdDate=row.get('createTime', None),
                modifiedDate=row.get('updateTime', None)
            )
            cargos.append(cargo)
        
        logger.info(f"Returned {len(cargos)} cargo categories (page {page}, limit {limit})")
        
        return CargoListResponse(
            code="1",
            message="Lấy dữ liệu thành công" if cargos else "Không có dữ liệu",
            data=cargos
        )
        
    except Exception as e:
        logger.error(f"Error fetching cargo categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


@app.get(
    "/api/cargoCategory/{cargo_id}",
    response_model=CargoSingleResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        404: {"description": "Không tìm thấy nhóm hàng"},
        401: {"description": "Chưa xác thực"}
    },
    summary="Lấy thông tin nhóm hàng hóa theo ID",
    tags=["Cargo Category"]
)
async def get_cargo_by_id(
    cargo_id: int,
    companyId: Optional[str] = Query(None, description="Mã công ty"),
    current_user = Depends(get_current_user)
):
    """
    Lấy thông tin chi tiết của một nhóm hàng hóa
    
    - **cargo_id**: Mã nhóm hàng
    - **companyId**: Mã công ty (optional)
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Cargo detail request for ID {cargo_id} by {current_user.username}")
    
    try:
        query = """
            SELECT 
                cargoId,
                cargoCode,
                cargoName,
                cargoGroupId,
                cargoGroupBillingId,
                customsHsCodeId,
                rowInvisible,
                rowDeleted,
                createUserId,
                updateUserId,
                createTime,
                updateTime,
                cargoGroupCode,
                cargoGroupName,
                cargoGroupDescription,
                cargoGroupBillingCode,
                cargoGroupBillingName,
                cargoGroupBillingDescription
            FROM dbo.vwCargo
            WHERE cargoId = ?
            AND rowDeleted = 0
        """
        
        results = db.execute_query(query, (cargo_id,))
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "0",
                    "message": "Không tìm thấy nhóm hàng hóa"
                }
            )
        
        row = results[0]
        cargo = CargoData(
            reportDate=datetime.now().strftime("%Y-%m-%d"),
            cargoId=row.get('cargoId', 0),
            cargoParentId=0,
            cargoTypeId=row.get('cargoGroupId', 0) or 0,
            cargoName=row.get('cargoName', '') or row.get('cargoGroupName', '') or '',
            createdDate=row.get('createTime', None),
            modifiedDate=row.get('updateTime', None)
        )
        
        logger.info(f"Cargo {cargo_id} found")
        
        return CargoSingleResponse(
            code="1",
            message="Lấy dữ liệu thành công",
            data=cargo
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching cargo {cargo_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


# Cargo Type API Endpoints

@app.get(
    "/api/cargoType",
    response_model=CargoTypeListResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        401: {"description": "Chưa xác thực"},
        500: {"description": "Lỗi server"}
    },
    summary="Lấy danh sách loại hàng hóa",
    tags=["Cargo Type"]
)
async def get_cargo_types(
    page: Optional[int] = Query(1, description="Trang hiện tại (pagination)", ge=1),
    limit: Optional[int] = Query(20, description="Số lượng records mỗi trang", ge=1, le=100),
    companyId: Optional[str] = Query(None, description="Mã công ty"),
    current_user = Depends(get_current_user)
):
    """
    Lấy danh sách các loại hàng hóa với phân trang
    
    - **page**: Trang hiện tại (default: 1)
    - **limit**: Số records mỗi trang (default: 20, max: 100)
    - **companyId**: Mã công ty (optional)
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Cargo type list request by {current_user.username}")
    
    try:
        # Query to get distinct cargo group types
        # Note: We use cargoGroupId and cargoGroupName to represent cargo types
        query = """
            SELECT DISTINCT
                cargoGroupId,
                cargoGroupCode,
                cargoGroupName,
                MIN(createTime) as createTime,
                MAX(updateTime) as updateTime
            FROM dbo.vwCargo
            WHERE rowDeleted = 0
            AND cargoGroupId IS NOT NULL
            AND cargoGroupName IS NOT NULL
            GROUP BY cargoGroupId, cargoGroupCode, cargoGroupName
        """
        
        params = []
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Add ordering and pagination
        query += " ORDER BY cargoGroupId OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])
        
        # Execute query
        results = db.execute_query(query, tuple(params) if params else None)
        
        # Transform to CargoTypeData format
        cargo_types = []
        for row in results:
            cargo_type = CargoTypeData(
                reportDate=datetime.now().strftime("%Y-%m-%d"),
                cargoTypeId=str(row.get('cargoGroupId', '') or row.get('cargoGroupCode', '')),
                cargoTypeName=row.get('cargoGroupName', '') or '',
                createdDate=row.get('createTime', None),
                modifiedDate=row.get('updateTime', None)
            )
            cargo_types.append(cargo_type)
        
        logger.info(f"Returned {len(cargo_types)} cargo types (page {page}, limit {limit})")
        
        return CargoTypeListResponse(
            code="1",
            message="Lấy dữ liệu thành công" if cargo_types else "Không có dữ liệu",
            data=cargo_types
        )
        
    except Exception as e:
        logger.error(f"Error fetching cargo types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


@app.get(
    "/api/cargoType/{cargo_type_id}",
    response_model=CargoTypeSingleResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        404: {"description": "Không tìm thấy loại hàng"},
        401: {"description": "Chưa xác thực"}
    },
    summary="Lấy thông tin loại hàng hóa theo ID",
    tags=["Cargo Type"]
)
async def get_cargo_type_by_id(
    cargo_type_id: str,
    companyId: Optional[str] = Query(None, description="Mã công ty"),
    current_user = Depends(get_current_user)
):
    """
    Lấy thông tin chi tiết của một loại hàng hóa
    
    - **cargo_type_id**: Mã loại hàng
    - **companyId**: Mã công ty (optional)
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Cargo type detail request for ID {cargo_type_id} by {current_user.username}")
    
    try:
        # Try to parse as int for cargoGroupId, otherwise search by code
        try:
            type_id_int = int(cargo_type_id)
            query = """
                SELECT DISTINCT
                    cargoGroupId,
                    cargoGroupCode,
                    cargoGroupName,
                    MIN(createTime) as createTime,
                    MAX(updateTime) as updateTime
                FROM dbo.vwCargo
                WHERE cargoGroupId = ?
                AND rowDeleted = 0
                GROUP BY cargoGroupId, cargoGroupCode, cargoGroupName
            """
            results = db.execute_query(query, (type_id_int,))
        except ValueError:
            # If not an int, search by code
            query = """
                SELECT DISTINCT
                    cargoGroupId,
                    cargoGroupCode,
                    cargoGroupName,
                    MIN(createTime) as createTime,
                    MAX(updateTime) as updateTime
                FROM dbo.vwCargo
                WHERE cargoGroupCode = ?
                AND rowDeleted = 0
                GROUP BY cargoGroupId, cargoGroupCode, cargoGroupName
            """
            results = db.execute_query(query, (cargo_type_id,))
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "0",
                    "message": "Không tìm thấy loại hàng hóa"
                }
            )
        
        row = results[0]
        cargo_type = CargoTypeData(
            reportDate=datetime.now().strftime("%Y-%m-%d"),
            cargoTypeId=str(row.get('cargoGroupId', '') or row.get('cargoGroupCode', '')),
            cargoTypeName=row.get('cargoGroupName', '') or '',
            createdDate=row.get('createTime', None),
            modifiedDate=row.get('updateTime', None)
        )
        
        logger.info(f"Cargo type {cargo_type_id} found")
        
        return CargoTypeSingleResponse(
            code="1",
            message="Lấy dữ liệu thành công",
            data=cargo_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching cargo type {cargo_type_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


# Handling Method List API Endpoints

@app.get(
    "/api/handlingMethodList",
    response_model=HandlingMethodListResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        401: {"description": "Chưa xác thực"},
        500: {"description": "Lỗi server"}
    },
    summary="Lấy danh sách phương án tác nghiệp",
    tags=["Handling Method"]
)
async def get_handling_methods(
    page: Optional[int] = Query(1, description="Trang hiện tại (pagination)", ge=1),
    limit: Optional[int] = Query(20, description="Số lượng records mỗi trang", ge=1, le=100),
    companyId: Optional[str] = Query(None, description="Mã công ty"),
    current_user = Depends(get_current_user)
):
    """
    Lấy danh sách các phương án tác nghiệp với phân trang
    
    - **page**: Trang hiện tại (default: 1)
    - **limit**: Số records mỗi trang (default: 20, max: 100)
    - **companyId**: Mã công ty (optional)
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Handling method list request by {current_user.username}")
    
    try:
        # Query to get distinct handling methods from vwTallyShiftAll
        # Use jobMethodCode and jobMethodName for handling method information
        query = """
            SELECT DISTINCT
                jobMethodCode,
                jobMethodName,
                MIN(createTime) as createTime,
                MAX(updateTime) as updateTime
            FROM dbo.vwTallyShiftAll
            WHERE rowDeleted IS NULL
            AND jobMethodCode IS NOT NULL
            AND jobMethodName IS NOT NULL
            GROUP BY jobMethodCode, jobMethodName
        """
        
        params = []
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Add ordering and pagination
        query += " ORDER BY jobMethodCode OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])
        
        # Execute query
        results = db.execute_query(query, tuple(params) if params else None)
        
        # Transform to HandlingMethodData format
        handling_methods = []
        for row in results:
            method = HandlingMethodData(
                reportDate=datetime.now().strftime("%Y-%m-%d"),
                handlingMethodId=str(row.get('jobMethodCode', '')),
                handlingMethodName=row.get('jobMethodName', '') or '',
                createdDate=row.get('createTime', None),
                modifiedDate=row.get('updateTime', None)
            )
            handling_methods.append(method)
        
        logger.info(f"Returned {len(handling_methods)} handling methods (page {page}, limit {limit})")
        
        return HandlingMethodListResponse(
            code="1",
            message="Lấy dữ liệu thành công" if handling_methods else "Không có dữ liệu",
            data=handling_methods
        )
        
    except Exception as e:
        logger.error(f"Error fetching handling methods: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


@app.get(
    "/api/handlingMethodList/{handling_method_id}",
    response_model=HandlingMethodSingleResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        404: {"description": "Không tìm thấy phương án tác nghiệp"},
        401: {"description": "Chưa xác thực"}
    },
    summary="Lấy thông tin phương án tác nghiệp theo ID",
    tags=["Handling Method"]
)
async def get_handling_method_by_id(
    handling_method_id: str,
    companyId: Optional[str] = Query(None, description="Mã công ty"),
    current_user = Depends(get_current_user)
):
    """
    Lấy thông tin chi tiết của một phương án tác nghiệp
    
    - **handling_method_id**: Mã phương án tác nghiệp
    - **companyId**: Mã công ty (optional)
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Handling method detail request for ID {handling_method_id} by {current_user.username}")
    
    try:
        query = """
            SELECT DISTINCT
                jobMethodCode,
                jobMethodName,
                MIN(createTime) as createTime,
                MAX(updateTime) as updateTime
            FROM dbo.vwTallyShiftAll
            WHERE rowDeleted IS NULL
            AND jobMethodCode = ?
            GROUP BY jobMethodCode, jobMethodName
        """
        
        results = db.execute_query(query, (handling_method_id,))
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "0",
                    "message": "Không tìm thấy phương án tác nghiệp"
                }
            )
        
        row = results[0]
        method = HandlingMethodData(
            reportDate=datetime.now().strftime("%Y-%m-%d"),
            handlingMethodId=str(row.get('jobMethodCode', '')),
            handlingMethodName=row.get('jobMethodName', '') or '',
            createdDate=row.get('createTime', None),
            modifiedDate=row.get('updateTime', None)
        )
        
        logger.info(f"Handling method {handling_method_id} found")
        
        return HandlingMethodSingleResponse(
            code="1",
            message="Lấy dữ liệu thành công",
            data=method
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching handling method {handling_method_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


# Class (Cargo Direction) API Endpoints

@app.get(
    "/api/class",
    response_model=ClassListResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        401: {"description": "Chưa xác thực"},
        500: {"description": "Lỗi server"}
    },
    summary="Lấy danh sách hướng tàu",
    tags=["Class"]
)
async def get_classes(
    page: Optional[int] = Query(1, description="Trang hiện tại (pagination)", ge=1),
    limit: Optional[int] = Query(20, description="Số lượng records mỗi trang", ge=1, le=100),
    companyId: Optional[str] = Query(None, description="Mã công ty"),
    current_user = Depends(get_current_user)
):
    """
    Lấy danh sách các hướng tàu với phân trang
    
    - **page**: Trang hiện tại (default: 1)
    - **limit**: Số records mỗi trang (default: 20, max: 100)
    - **companyId**: Mã công ty (optional)
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Class list request by {current_user.username}")
    
    try:
        # Query to get distinct classes (cargo directions) from vwTallyShiftAll
        # vwTallyShiftAll uses NULL for active records, not 0
        query = """
            SELECT DISTINCT
                cargoDirectCode,
                cargoDirectName,
                MIN(createTime) as createTime,
                MAX(updateTime) as updateTime
            FROM dbo.vwTallyShiftAll
            WHERE rowDeleted IS NULL
            AND cargoDirectCode IS NOT NULL
            AND cargoDirectName IS NOT NULL
            GROUP BY cargoDirectCode, cargoDirectName
        """
        
        params = []
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Add ordering and pagination
        query += " ORDER BY cargoDirectCode OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])
        
        # Execute query
        results = db.execute_query(query, tuple(params) if params else None)
        
        # Transform to ClassData format
        classes = []
        for row in results:
            class_item = ClassData(
                reportDate=datetime.now().strftime("%Y-%m-%d"),
                classId=str(row.get('cargoDirectCode', '')),
                className=row.get('cargoDirectName', '') or '',
                createdDate=row.get('createTime', None),
                modifiedDate=row.get('updateTime', None)
            )
            classes.append(class_item)
        
        logger.info(f"Returned {len(classes)} classes (page {page}, limit {limit})")
        
        return ClassListResponse(
            code="1",
            message="Lấy dữ liệu thành công" if classes else "Không có dữ liệu",
            data=classes
        )
        
    except Exception as e:
        logger.error(f"Error fetching classes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


@app.get(
    "/api/class/{class_id}",
    response_model=ClassSingleResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        404: {"description": "Không tìm thấy hướng tàu"},
        401: {"description": "Chưa xác thực"}
    },
    summary="Lấy thông tin hướng tàu theo ID",
    tags=["Class"]
)
async def get_class_by_id(
    class_id: str,
    companyId: Optional[str] = Query(None, description="Mã công ty"),
    current_user = Depends(get_current_user)
):
    """
    Lấy thông tin chi tiết của một hướng tàu
    
    - **class_id**: Mã hướng tàu (cargoDirectCode)
    - **companyId**: Mã công ty (optional)
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Class detail request for ID {class_id} by {current_user.username}")
    
    try:
        query = """
            SELECT DISTINCT
                cargoDirectCode,
                cargoDirectName,
                MIN(createTime) as createTime,
                MAX(updateTime) as updateTime
            FROM dbo.vwTallyShiftAll
            WHERE rowDeleted IS NULL
            AND cargoDirectCode = ?
            GROUP BY cargoDirectCode, cargoDirectName
        """
        
        results = db.execute_query(query, (class_id,))
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "0",
                    "message": "Không tìm thấy hướng tàu"
                }
            )
        
        row = results[0]
        class_item = ClassData(
            reportDate=datetime.now().strftime("%Y-%m-%d"),
            classId=str(row.get('cargoDirectCode', '')),
            className=row.get('cargoDirectName', '') or '',
            createdDate=row.get('createTime', None),
            modifiedDate=row.get('updateTime', None)
        )
        
        logger.info(f"Class {class_id} found")
        
        return ClassSingleResponse(
            code="1",
            message="Lấy dữ liệu thành công",
            data=class_item
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching class {class_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


# Ship Details API Endpoints

@app.get(
    "/api/shipDetails",
    response_model=ShipListResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        401: {"description": "Chưa xác thực"},
        500: {"description": "Lỗi server"}
    },
    summary="Lấy danh sách tàu",
    tags=["Ship Details"]
)
async def get_ships(
    page: Optional[int] = Query(1, description="Trang hiện tại (pagination)", ge=1),
    limit: Optional[int] = Query(20, description="Số lượng records mỗi trang", ge=1, le=100),
    companyId: Optional[str] = Query(None, description="Mã công ty"),
    current_user = Depends(get_current_user)
):
    """
    Lấy danh sách các tàu với phân trang
    
    - **page**: Trang hiện tại (default: 1)
    - **limit**: Số records mỗi trang (default: 20, max: 100)
    - **companyId**: Mã công ty (optional)
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Ship list request by {current_user.username}")
    
    try:
        # Query to get ships from dbo.Vessel
        # Pattern 1: rowDeleted = 0 for active records
        query = """
            SELECT
                vesselId,
                vesselCode,
                vesselName,
                numberIMO,
                vesselTypeId,
                countryId,
                vesselGT,
                vesselBEAM,
                vesselLOA,
                vesselDWT,
                ownerId,
                createTime,
                updateTime
            FROM dbo.Vessel
            WHERE rowDeleted = 0
        """
        
        params = []
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Add ordering and pagination
        query += " ORDER BY vesselId OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])
        
        # Execute query
        results = db.execute_query(query, tuple(params) if params else None)
        
        # Transform to ShipData format
        ships = []
        for row in results:
            ship_item = ShipData(
                reportDate=datetime.now().strftime("%Y-%m-%d"),
                shipId=str(row.get('vesselId', '')),
                shipIMO=row.get('numberIMO', '') or '',
                shipFullName=row.get('vesselName', '') or '',
                shipGroup='',  # No equivalent column in actual schema
                flagState=str(row.get('countryId', '')) if row.get('countryId') else '',
                shipLOA=str(row.get('vesselLOA', '')) if row.get('vesselLOA') else None,
                shipBeam=str(row.get('vesselBEAM', '')) if row.get('vesselBEAM') else None,
                shipGRT=str(row.get('vesselGT', '')) if row.get('vesselGT') else None,
                shipType=str(row.get('vesselTypeId', '')) if row.get('vesselTypeId') else None,
                shipDWT=str(row.get('vesselDWT', '')) if row.get('vesselDWT') else None,
                shipOwner=str(row.get('ownerId', '')) if row.get('ownerId') else None,
                createdDate=row.get('createTime').strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z" if row.get('createTime') and hasattr(row.get('createTime'), 'strftime') else str(row.get('createTime')) if row.get('createTime') else None,
                modifiedDate=row.get('updateTime').strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z" if row.get('updateTime') and hasattr(row.get('updateTime'), 'strftime') else str(row.get('updateTime')) if row.get('updateTime') else None
            )
            ships.append(ship_item)
        
        logger.info(f"Returned {len(ships)} ships (page {page}, limit {limit})")
        
        return ShipListResponse(
            code="1",
            message="Lấy dữ liệu thành công" if ships else "Không có dữ liệu",
            data=ships
        )
        
    except Exception as e:
        logger.error(f"Error fetching ships: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


@app.get(
    "/api/shipDetails/{ship_imo}",
    response_model=ShipSingleResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        404: {"description": "Không tìm thấy tàu"},
        401: {"description": "Chưa xác thực"}
    },
    summary="Lấy thông tin tàu theo IMO",
    tags=["Ship Details"]
)
async def get_ship_by_imo(
    ship_imo: str,
    companyId: Optional[str] = Query(None, description="Mã công ty"),
    current_user = Depends(get_current_user)
):
    """
    Lấy thông tin chi tiết của một tàu
    
    - **ship_imo**: Mã IMO của tàu (vesselCode)
    - **companyId**: Mã công ty (optional)
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Ship detail request for IMO {ship_imo} by {current_user.username}")
    
    try:
        query = """
            SELECT
                vesselId,
                vesselCode,
                vesselName,
                numberIMO,
                vesselTypeId,
                countryId,
                vesselGT,
                vesselBEAM,
                vesselLOA,
                vesselDWT,
                ownerId,
                createTime,
                updateTime
            FROM dbo.Vessel
            WHERE rowDeleted = 0
            AND numberIMO = ?
        """
        
        results = db.execute_query(query, (ship_imo,))
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "0",
                    "message": "Không tìm thấy tàu"
                }
            )
        
        row = results[0]
        ship_item = ShipData(
            reportDate=datetime.now().strftime("%Y-%m-%d"),
            shipId=str(row.get('vesselId', '')),
            shipIMO=row.get('numberIMO', '') or '',
            shipFullName=row.get('vesselName', '') or '',
            shipGroup='',  # No equivalent column in actual schema
            flagState=str(row.get('countryId', '')) if row.get('countryId') else '',
            shipLOA=str(row.get('vesselLOA', '')) if row.get('vesselLOA') else None,
            shipBeam=str(row.get('vesselBEAM', '')) if row.get('vesselBEAM') else None,
            shipGRT=str(row.get('vesselGT', '')) if row.get('vesselGT') else None,
            shipType=str(row.get('vesselTypeId', '')) if row.get('vesselTypeId') else None,
            shipDWT=str(row.get('vesselDWT', '')) if row.get('vesselDWT') else None,
            shipOwner=str(row.get('ownerId', '')) if row.get('ownerId') else None,
            createdDate=row.get('createTime').strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z" if row.get('createTime') and hasattr(row.get('createTime'), 'strftime') else str(row.get('createTime')) if row.get('createTime') else None,
            modifiedDate=row.get('updateTime').strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z" if row.get('updateTime') and hasattr(row.get('updateTime'), 'strftime') else str(row.get('updateTime')) if row.get('updateTime') else None
        )
        
        logger.info(f"Ship {ship_imo} found")
        
        return ShipSingleResponse(
            code="1",
            message="Lấy dữ liệu thành công",
            data=ship_item
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ship {ship_imo}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


# Bulk Gate Volumes API Endpoint

@app.get(
    "/api/bulkGateVolumesCB",
    response_model=BulkGateVolumeListResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        401: {"description": "Chưa xác thực"},
        500: {"description": "Lỗi server"}
    },
    summary="Lấy toàn bộ các bản ghi sản lượng (với filter)",
    tags=["Bulk Gate Volumes"]
)
async def get_bulk_gate_volumes(
    startDate: Optional[str] = Query(None, description="Lọc record với trường finishDate, sử dụng để lấy những record bắt đầu từ finishDate"),
    endDate: Optional[str] = Query(None, description="Lọc record với trường finishDate, sử dụng để lấy những record có ngày kết thúc là finishDate"),
    companyId: Optional[str] = Query(None, description="Lọc các bản ghi theo đơn vị công ty"),
    handlingMethodId: Optional[str] = Query(None, description="Lọc các bản ghi theo phương án xếp dỡ"),
    page: Optional[int] = Query(1, description="Page number cho phần trang (pagination)", ge=1),
    limit: Optional[int] = Query(20, description="Số lượng record mỗi trang (max 100)", ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """
    API cung cấp sản lượng hàng rời theo qua cổng cảng và kho bãi
    
    **Filters applied:**
    - vesselCode LIKE '%BÃI%' OR vesselCode LIKE '%KHO%'
    - weightNetSum > 0
    - rowDeleted IS NULL (active records only)
    - Optional: startDate, endDate, companyId, handlingMethodId
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Bulk gate volumes request by {current_user.username}")
    
    try:
        # Base query for bulk gate volumes from vwTallyShiftAll
        # Pattern 2: rowDeleted IS NULL for active records
        query = """
            SELECT
                t.shiftDate,
                t.tallyShiftId,
                t.consigneeId,
                t.consigneeCode,
                t.cargoId,
                t.jobMethodId,
                t.vesselId,
                t.weightNetSum,
                c.cargoGroupId,
                t.createTime,
                t.updateTime
            FROM dbo.vwTallyShiftAll t
            LEFT JOIN dbo.vwCargo c ON t.cargoId = c.cargoId
            WHERE t.rowDeleted IS NULL
            AND t.weightNetSum > 0
            AND (t.vesselCode LIKE ? OR t.vesselCode LIKE ?)
        """
        
        params = ['%BÃI%', '%KHO%']
        
        # Add optional filters
        if startDate:
            query += " AND t.shiftDate >= ?"
            params.append(startDate)
        
        if endDate:
            query += " AND t.shiftDate <= ?"
            params.append(endDate)
        
        if companyId:
            # companyId filter - assuming it maps to a specific field
            # Adjust if needed based on actual schema
            query += " AND t.consigneeId = ?"
            params.append(companyId)
        
        if handlingMethodId:
            query += " AND t.jobMethodId = ?"
            params.append(handlingMethodId)
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Add ordering and pagination
        query += " ORDER BY t.shiftDate DESC, t.tallyShiftId OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])
        
        # Execute query
        results = db.execute_query(query, tuple(params))
        
        # Transform to BulkGateVolumeData format
        volumes = []
        for row in results:
            volume_item = BulkGateVolumeData(
                reportDate=datetime.now().strftime("%Y-%m-%d"),
                finishDate=row.get('shiftDate').strftime("%Y-%m-%d") if row.get('shiftDate') and hasattr(row.get('shiftDate'), 'strftime') else str(row.get('shiftDate')) if row.get('shiftDate') else '',
                companyId=str(row.get('consigneeId', '')) if row.get('consigneeId') else '',
                cargoTypeId=str(row.get('cargoGroupId', '')) if row.get('cargoGroupId') else '',
                cargoCategoryId=str(row.get('cargoId', '')) if row.get('cargoId') else '',
                handlingMethodId=str(row.get('jobMethodId', '')) if row.get('jobMethodId') else '',
                bulkOriginId=str(row.get('vesselId', '')) if row.get('vesselId') else '',
                bulkWeight=float(row.get('weightNetSum', 0)) if row.get('weightNetSum') else 0.0,
                customerCode=row.get('consigneeCode', '') or ''
            )
            volumes.append(volume_item)
        
        logger.info(f"Returned {len(volumes)} bulk gate volume records (page {page}, limit {limit})")
        
        return BulkGateVolumeListResponse(
            code="1",
            message="Lấy dữ liệu thành công" if volumes else "Không có dữ liệu",
            data=volumes
        )
        
    except Exception as e:
        logger.error(f"Error fetching bulk gate volumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


# Bulk Quay Volumes API Endpoint

@app.get(
    "/api/bulkQuayVolumesCB",
    response_model=BulkQuayVolumeListResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        401: {"description": "Chưa xác thực"},
        500: {"description": "Lỗi server"}
    },
    summary="Lấy toàn bộ các bản ghi sản lượng (với filter)",
    tags=["Bulk Quay Volumes"]
)
async def get_bulk_quay_volumes(
    startDate: Optional[str] = Query(None, description="Lọc record với trường finishDate, sử dụng để lấy những record bắt đầu từ finishDate"),
    endDate: Optional[str] = Query(None, description="Lọc record với trường finishDate, sử dụng để lấy những record có ngày kết thúc là finishDate"),
    companyId: Optional[str] = Query(None, description="Lọc các bản ghi theo đơn vị công ty"),
    shipId: Optional[str] = Query(None, description="Lọc các bản ghi theo tàu chở hàng rời"),
    handlingMethodId: Optional[str] = Query(None, description="Lọc các bản ghi theo phương án xếp dỡ"),
    page: Optional[int] = Query(1, description="Page number cho phần trang (pagination)", ge=1),
    limit: Optional[int] = Query(20, description="Số lượng record mỗi trang (max 100)", ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """
    API cung cấp sản lượng hàng rời tại cầu tàu/bến (không bao gồm container)
    
    **Filters applied:**
    - jobMethodCode LIKE '%TAU%' (ship operations)
    - cargoGroupCode <> 'Container' (exclude containers)
    - weightNetSum > 0
    - rowDeleted IS NULL (active records only)
    - Optional: startDate, endDate, companyId, shipId, handlingMethodId
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Bulk quay volumes request by {current_user.username}")
    
    try:
        # Base query for bulk quay volumes from vwTallyShiftAll
        # Pattern 2: rowDeleted IS NULL for active records
        # Need to join with vwCargo to filter out Container cargo
        query = """
            SELECT
                t.shiftDate,
                t.tallyShiftId,
                t.consigneeId,
                t.consigneeCode,
                t.cargoId,
                t.jobMethodId,
                t.vesselId,
                t.agencyId,
                t.cargoDirectId,
                t.weightNetSum,
                c.cargoGroupCode,
                c.cargoGroupId,
                t.createTime,
                t.updateTime
            FROM dbo.vwTallyShiftAll t
            LEFT JOIN dbo.vwCargo c ON t.cargoId = c.cargoId
            WHERE t.rowDeleted IS NULL
            AND t.weightNetSum > 0
            AND t.jobMethodCode LIKE ?
            AND (c.cargoGroupCode IS NULL OR c.cargoGroupCode <> 'Container')
        """
        
        params = ['%TAU%']
        
        # Add optional filters
        if startDate:
            query += " AND t.shiftDate >= ?"
            params.append(startDate)
        
        if endDate:
            query += " AND t.shiftDate <= ?"
            params.append(endDate)
        
        if companyId:
            query += " AND t.consigneeId = ?"
            params.append(companyId)
        
        if shipId:
            query += " AND t.vesselId = ?"
            params.append(shipId)
        
        if handlingMethodId:
            query += " AND t.jobMethodId = ?"
            params.append(handlingMethodId)
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Add ordering and pagination
        query += " ORDER BY t.shiftDate DESC, t.tallyShiftId OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])
        
        # Execute query
        results = db.execute_query(query, tuple(params))
        
        # Transform to BulkQuayVolumeData format
        volumes = []
        for row in results:
            volume_item = BulkQuayVolumeData(
                reportDate=datetime.now().strftime("%Y-%m-%d"),
                finishDate=row.get('shiftDate').strftime("%Y-%m-%d") if row.get('shiftDate') and hasattr(row.get('shiftDate'), 'strftime') else str(row.get('shiftDate')) if row.get('shiftDate') else '',
                companyId=str(row.get('consigneeId', '')) if row.get('consigneeId') else '',
                shipId=str(row.get('vesselId', '')) if row.get('vesselId') else '',
                shipAgentId=str(row.get('agencyId', '')) if row.get('agencyId') else '',
                cargoTypeId=str(row.get('cargoGroupId', '')) if row.get('cargoGroupId') else '',
                cargoCategoryId=str(row.get('cargoId', '')) if row.get('cargoId') else '',
                handlingMethodId=str(row.get('jobMethodId', '')) if row.get('jobMethodId') else '',
                shipClassId=str(row.get('cargoDirectId', '')) if row.get('cargoDirectId') else '',
                bulkOriginId=str(row.get('vesselId', '')) if row.get('vesselId') else '',
                bulkWeight=float(row.get('weightNetSum', 0)) if row.get('weightNetSum') else 0.0
            )
            volumes.append(volume_item)
        
        logger.info(f"Returned {len(volumes)} bulk quay volume records (page {page}, limit {limit})")
        
        return BulkQuayVolumeListResponse(
            code="1",
            message="Lấy dữ liệu thành công" if volumes else "Không có dữ liệu",
            data=volumes
        )
        
    except Exception as e:
        logger.error(f"Error fetching bulk quay volumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


# Container Quay Volumes API Endpoint

@app.get(
    "/api/contQuayVolumesCB",
    response_model=ContainerQuayVolumeListResponse,
    responses={
        200: {"description": "Lấy dữ liệu thành công"},
        401: {"description": "Chưa xác thực"},
        500: {"description": "Lỗi server"}
    },
    summary="Lấy toàn bộ các bản ghi sản lượng container (với filter)",
    tags=["Container Quay Volumes"]
)
async def get_container_quay_volumes(
    startDate: Optional[str] = Query(None, description="Lọc record với trường finishDate, sử dụng để lấy những record bắt đầu từ finishDate"),
    endDate: Optional[str] = Query(None, description="Lọc record với trường finishDate, sử dụng để lấy những record có ngày kết thúc là finishDate"),
    companyId: Optional[str] = Query(None, description="Lọc các bản ghi theo đơn vị công ty"),
    shipId: Optional[str] = Query(None, description="Lọc các bản ghi theo tàu chở hàng"),
    handlingMethodId: Optional[str] = Query(None, description="Lọc các bản ghi theo phương án xếp dỡ"),
    page: Optional[int] = Query(1, description="Page number cho phần trang (pagination)", ge=1),
    limit: Optional[int] = Query(20, description="Số lượng record mỗi trang (max 100)", ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """
    API cung cấp sản lượng container tại cầu tàu/bến
    
    **Filters applied:**
    - jobMethodCode LIKE '%TAU%' (ship operations)
    - cargoGroupCode = 'Hàng Container' (ONLY containers)
    - weightNetSum > 0
    - rowDeleted IS NULL (active records only)
    - Optional: startDate, endDate, companyId, shipId, handlingMethodId
    
    **Yêu cầu**: Bearer token từ /api/login
    """
    logger.info(f"Container quay volumes request by {current_user.username}")
    
    try:
        # Base query for container quay volumes from vwTallyShiftAll
        # Pattern 2: rowDeleted IS NULL for active records
        # Join with vwCargo to filter ONLY Container cargo
        query = """
            SELECT
                t.shiftDate,
                t.tallyShiftId,
                t.consigneeId,
                t.consigneeCode,
                t.cargoId,
                t.jobMethodId,
                t.vesselId,
                t.agencyId,
                t.cargoDirectId,
                t.weightNetSum,
                t.quantityTotalSum,
                c.cargoGroupCode,
                c.cargoGroupId,
                t.createTime,
                t.updateTime
            FROM dbo.vwTallyShiftAll t
            LEFT JOIN dbo.vwCargo c ON t.cargoId = c.cargoId
            WHERE t.rowDeleted IS NULL
            AND t.weightNetSum > 0
            AND t.jobMethodCode LIKE ?
            AND c.cargoGroupCode = 'Hàng Container'
        """
        
        params = ['%TAU%']
        
        # Add optional filters
        if startDate:
            query += " AND t.shiftDate >= ?"
            params.append(startDate)
        
        if endDate:
            query += " AND t.shiftDate <= ?"
            params.append(endDate)
        
        if companyId:
            query += " AND t.consigneeId = ?"
            params.append(companyId)
        
        if shipId:
            query += " AND t.vesselId = ?"
            params.append(shipId)
        
        if handlingMethodId:
            query += " AND t.jobMethodId = ?"
            params.append(handlingMethodId)
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Add ordering and pagination
        query += " ORDER BY t.shiftDate DESC, t.tallyShiftId OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])
        
        # Execute query
        results = db.execute_query(query, tuple(params))
        
        # Transform to ContainerQuayVolumeData format
        volumes = []
        for row in results:
            volume_item = ContainerQuayVolumeData(
                reportDate=datetime.now().strftime("%Y-%m-%d"),
                companyId=str(row.get('consigneeId', '')) if row.get('consigneeId') else '',
                shipId=str(row.get('vesselId', '')) if row.get('vesselId') else '',
                classId=str(row.get('cargoDirectId', '')) if row.get('cargoDirectId') else '',
                originId=str(row.get('vesselId', '')) if row.get('vesselId') else '',  # Can be adjusted based on requirements
                containerWeight=float(row.get('weightNetSum', 0)) if row.get('weightNetSum') else 0.0,
                containerTEU=int(row.get('quantityTotalSum', 0)) if row.get('quantityTotalSum') else 0,
                handlingMethodId=str(row.get('jobMethodId', '')) if row.get('jobMethodId') else '',
                finishDate=row.get('shiftDate').strftime("%Y-%m-%d") if row.get('shiftDate') and hasattr(row.get('shiftDate'), 'strftime') else str(row.get('shiftDate')) if row.get('shiftDate') else '',
                shipOperatorId=str(row.get('consigneeCode', '')) if row.get('consigneeCode') else '',
                containerOperatorId=str(row.get('consigneeId', '')) if row.get('consigneeId') else ''
            )
            volumes.append(volume_item)
        
        logger.info(f"Returned {len(volumes)} container quay volume records (page {page}, limit {limit})")
        
        return ContainerQuayVolumeListResponse(
            code="1",
            message="Lấy dữ liệu thành công" if volumes else "Không có dữ liệu",
            data=volumes
        )
        
    except Exception as e:
        logger.error(f"Error fetching container quay volumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "0",
                "message": f"Lỗi lấy dữ liệu: {str(e)}"
            }
        )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting TOS Big Data API Server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

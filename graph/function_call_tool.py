import json
from langchain_core.tools import tool

# mock tools
@tool
def get_shipping_info(product:str) -> str:
    """주문한 상품에 대한 배송 정보 조회
    
    Args:
        product: 상품명"""
    shipping_info = "배송준비중"
    return shipping_info

@tool
def get_grade_info() -> str:
    """유저의 등급 조회"""
    grade = "VIP"
    return grade

@tool
def get_order_info() -> list:
    """주문한 상품 정보 조회"""
    orders = [
        {
            "name":"스트라이프 셔츠",
            "price":"12,000원"
        },
        {
            "name":"트레이닝 바지",
            "price":"35,000원"
        }
    ]
    return orders

tools = [get_order_info, get_shipping_info, get_grade_info]


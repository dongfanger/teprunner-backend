from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def search_sku(request, *args, **kwargs):
    return Response({"skuId": "222", "price": "2.3"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def add_cart(request, *args, **kwargs):
    return Response({"skuId": "222", "price": "2.3", "skuNum": "3", "totalPrice": "6.9"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def order(request, *args, **kwargs):
    return Response({"orderId": "333"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def pay(request, *args, **kwargs):
    return Response({"success": "true"}, status=status.HTTP_200_OK)

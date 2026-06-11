import json
import re
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Enquiry, EnquiryItem


def enquiry_page(request):
    return render(request, 'enquiry.html')


@csrf_exempt
@require_POST
def submit_enquiry(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # Validate required fields
    errors = {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()
    city = (data.get('city') or '').strip()
    state = (data.get('state') or '').strip()
    items = data.get('items') or []

    if not name:
        errors['name'] = 'Name is required.'
    if not email or '@' not in email:
        errors['email'] = 'Valid email is required.'
    if not phone or not re.match(r'^[\d\s\+\(\)\-]{7,20}$', phone):
        errors['phone'] = 'Valid phone number is required.'
    if not items:
        errors['items'] = 'At least one product is required.'

    if errors:
        return JsonResponse({'errors': errors}, status=400)

    btype_map = {
        'dealer': 'dealer', 'distributor': 'distributor',
        'retailer': 'retailer', 'customer': 'customer', 'other': 'other',
    }
    business_type = btype_map.get((data.get('businessType') or 'Customer').lower(), 'customer')

    enquiry = Enquiry.objects.create(
        full_name=name,
        email=email,
        phone=phone,
        city=city,
        state=state,
        country=data.get('country') or 'India',
        business_type=business_type,
        company_name=data.get('company') or '',
        message=data.get('message') or '',
    )

    from products.models import Product
    for item in items:
        slug = item.get('id') or ''
        product_obj = Product.objects.filter(slug=slug).first() if slug else None
        EnquiryItem.objects.create(
            enquiry=enquiry,
            product=product_obj,
            product_name=item.get('name') or '',
            product_sku=item.get('sku') or '',
            quantity=int(item.get('qty') or 1),
        )

    return JsonResponse({'ref_number': enquiry.ref_number, 'message': 'Enquiry submitted successfully.'})

from django.contrib.auth.decorators import login_required

from django.shortcuts import render




@login_required
def dashbaord(request):
    return render(request, 'dashboard/dashboard.html')
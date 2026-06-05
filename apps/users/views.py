from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout

from django.shortcuts import render
from django.shortcuts import redirect


def login_view(request):

    if request.method == 'POST':

        email = request.POST.get('email')

        password = request.POST.get('password')

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:

            login(request, user)

            if user.role == 'ADMIN':

                return redirect('/admin-dashboard/')


            elif user.role == 'HEAD':

                return redirect('/head-dashboard/')


            elif user.role == 'TEACHER':

                return redirect('/teacher-dashboard/')


            elif user.role == 'STUDY_MASTER':

                return redirect('/study-dashboard/')

            return redirect('/')

        messages.error(
            request,
            'Неверный email или пароль'
        )

    return render(
        request,
        'auth/login.html'
    )


def logout_view(request):

    logout(request)

    return redirect('/login/')
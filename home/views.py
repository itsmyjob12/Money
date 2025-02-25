from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from authentication.models import User, Profile
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import MarqueVoiture, Modele, Conducteur, Voiture
import json
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string


@login_required(login_url="/login/")
def index(request):
    nombre_conducteur = Conducteur.objects.count()
    marques = MarqueVoiture.objects.all()
    nombre_Voiture = Voiture.objects.count()
    connected_profiles = Profile.objects.filter(is_online=True)
    nombre_profile = Profile.objects.count()
    return render(request,'home/index.html' ,{'nombre_conducteur': nombre_conducteur, 'nombre_Voiture': nombre_Voiture, 'nombre_profile': nombre_profile, 'connected_profiles': connected_profiles}) 

    context = {'segment': 'index', 'marques':marques}

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


# @login_required(login_url="/login/")
# def pages(request):
#     context = {}
#     # All resource paths end in .html.
#     # Pick out the html file name from the url. And load that template.
#     try:
#         load_template = request.path.split('/')[-1]

#         if load_template == 'admin':
#             return HttpResponseRedirect(reverse('admin:index'))
#         context['segment'] = load_template

#         html_template = loader.get_template('home/' + load_template)
#         return HttpResponse(html_template.render(context, request))

#     except template.TemplateDoesNotExist:

#         html_template = loader.get_template('home/page-404.html')
#         return HttpResponse(html_template.render(context, request))

#     except:
#         html_template = loader.get_template('home/page-500.html')
#         return HttpResponse(html_template.render(context, request))


def new_voiture(request):
    marques = MarqueVoiture.objects.all()
    modeles = Modele.objects.all()
    # Création d'un dictionnaire pour stocker les modèles de voitures
    # Ce dictionnaire sera renvoyé en JSON pour le filtrage des modèles selon la marque sélectionnée
    modeles_data = {}
    for modele in modeles:
        if modele.marque_id not in modeles_data:
            modeles_data[modele.marque_id] = []
        modeles_data[modele.marque_id].append({'id': modele.id, 'nom': modele.nom})

    if request.method == "POST":
        marque_voiture_id = request.POST.get("marque_voiture")
        modele_voiture_id = request.POST.get("modele")
        # Vérification des valeurs non vides
        if not marque_voiture_id:
            messages.error(request, "Veuillez sélectionner une marque de voiture.")
            return redirect('home/ajout/vehicule/')
        if not modele_voiture_id:
            messages.error(request, "Veuillez sélectionner un modèle de voiture.")
            return redirect('home/ajout/vehicule/')

        immatriculation = request.POST.get("immatriculation")
        numero_serie = request.POST.get("numero_serie")
        couleur_voiture = request.POST.get("couleur_voiture")
        photo_voiture = request.FILES.get("photo_voiture")
        annee_fabrication = request.POST.get("annee_fabrication")
        kilometrage = request.POST.get("kilometrage")
        type_carburant = request.POST.get("type_carburant")
        transmission = request.POST.get("transmission")
        symptomes = request.POST.get("symptomes")
        historique_maintenance = request.POST.get("historique_maintenance")
        codes_erreur = request.POST.get("codes_erreur")
        numero_chassi = request.POST.get("numero_chassi")
        nombre_de_vitesse = request.POST.get("nombre_de_vitesse")

        try:
            marque_voiture_obj = MarqueVoiture.objects.get(pk=marque_voiture_id)
        except MarqueVoiture.DoesNotExist:
            messages.error(request, "La marque sélectionnée n'existe pas.")
            return redirect('home/ajout/vehicule/')
        try:
            modele_voiture_obj = Modele.objects.get(pk=modele_voiture_id)
        except Modele.DoesNotExist:
            messages.error(request, "Le modèle sélectionné n'existe pas.")
            return redirect('home/ajout/vehicule/')

        add_voiture = Voiture(
            modele=modele_voiture_obj,
            annee_fabrication=annee_fabrication,
            kilometrage=kilometrage,
            type_carburant=type_carburant,
            transmission=transmission,
            numero_serie=numero_serie,
            immatriculation=immatriculation,
            couleur_voiture=couleur_voiture,
            symptomes=symptomes,
            historique_maintenance=historique_maintenance,
            codes_erreur=codes_erreur,
            numero_chassi=numero_chassi,
            nombre_de_vitesse=nombre_de_vitesse,
            photo_voiture=photo_voiture,
        )

        if photo_voiture:
            add_voiture.photo_voiture = photo_voiture

        add_voiture.save()
        messages.success(request, f'Voiture {add_voiture.modele} a été bien ajoutée!')
        return redirect('liste_voiture')

    datas = {
        'marques': marques,
        'modeles': modeles,
        # Envoi du dictionnaire en JSON
        'modeles_data': json.dumps(modeles_data),
    }
    return render(request, 'home/Ajout-vehicule.html', datas)


def new_conducteur(request):
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        adresse = request.POST.get('adresse')
        telephone = request.POST.get('telephone')
        site_web = request.POST.get('site_web')
        email = request.POST.get('email').strip()
        photo_conducteur = request.FILES.get('photo_conducteur')

        # Valider les champs obligatoires
        if not name or not email:
            return HttpResponseBadRequest("Name and email are required.")

        # Créer un compte utilisateur pour le conducteur
        username = name.replace(' ', '_').lower()
        password = User.objects.make_random_password()
        user = User.objects.create_user(username=username, email=email, password=password)

        # Créer le conducteur
        new_conducteur = Conducteur.objects.create(
            name=name,
            adresse=adresse,
            telephone=telephone,
            site_web=site_web,
            email=email,
            photo_conducteur=photo_conducteur,
            user=user,
        )

        # Envoyer un e-mail avec les informations de connexion au conducteur
        subject = 'Your conducteur Account Password'
        login_url = request.build_absolute_uri(reverse('activate_conducteur', args=[user.id]))
        message = f'Dear {name},\n\nYour conducteur account has been created successfully. Your username is {username} and your password is {password}. You can log in to your account at {login_url}.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

        return redirect('home')  # Rediriger vers une page appropriée après la création

    return render(request, 'home/Ajout-conducteur.html')

def activate_conducteur_role(request, user_id):
    if request.method == 'GET':
        try:
            user = get_user_model().objects.get(id=user_id)
            user.role = 'conducteur'
            user.save()
            return redirect('login_conducteur')  
        except get_user_model().DoesNotExist:
            return HttpResponseBadRequest("Invalid user ID")
    else:
        return HttpResponseBadRequest("Method not allowed")


#  liste des conducteurs
def list_conducteur(request):
    conducteurs = Conducteur.objects.all().order_by('-id')
    datas = {
        'conducteurs': conducteurs,
    }
    return render(request, 'home/liste-conducteur.html', datas)


def list_voitures(request):
    voitures = Voiture.objects.all().order_by('-id')
    datas = {
        'voitures': voitures,
    }
    return render(request, 'home/liste-vehicule.html', datas)



def detail_conducteurs(request, conducteur_id):
    conducteurs = Conducteur.objects.get(id=conducteur_id)
    datas = {
        'conducteurs': conducteurs,
    }
    return render(request, 'home/conducteur.html', datas)


def detail_voiture(request, voiture_id):
    voitures = Voiture.objects.get(id=voiture_id)
    datas = {
        'voitures': voitures,
    }
    return render(request, 'home/vehicule.html', datas)


def dashboard_particulier(request):
    user = request.user
    # Ajoutez ici la logique spécifique aux particuliers
    voitures = Voiture.objects.filter(owner=user)
    diagnostics = Diagnostic.objects.filter(voiture__owner=user)

    context = {
        'voitures': voitures,
        'diagnostics': diagnostics,
        'user': user,
    }
    return render(request, 'home/dashboard_particulier.html', context)

def profile(request):
    # Votre logique pour la vue profile
    return render(request, 'home/profile.html')


#  affecter une voiture à un conducteur 
def affect_voiture(request, voiture_id):
    voiture = get_object_or_404(Voiture, pk=voiture_id)
    conducteurs = Conducteur.objects.all()

    if request.method == 'POST':
        conducteur_id = request.POST.get('conducteur')
        try:
            conducteur = Conducteur.objects.get(pk=conducteur_id)
        except conducteur.DoesNotExist:
            messages.error(request, "Le conducteur sélectionné n'existe pas.")
            return redirect('affect_voiture', voiture_id=voiture_id)
    
     # Vérifiez si la voiture est déjà affectée à ce conducteur
        if voiture.conducteur_assigne == conducteur:
            messages.error(request, f"La voiture {voiture.modele} est déjà affectée au conducteur {conducteur.name}.")
            return redirect('affect_voiture', voiture_id=voiture_id)

        voiture.conducteur_assigne = conducteur
        voiture.statut = 'en attente de diagnostic'
        voiture.save()
        
        data = {
            'voiture': voiture,
            'conducteur': conducteur
        }
       
        # Envoyer un email au conducteur
        subject = 'Nouvelle voiture affectée pour diagnostic'
        message = f'Une nouvelle voiture a été affectée à votre conducteur pour diagnostic.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [conducteur.email]
        notice_html = render_to_string('home/emailAffect.html', data)
        send_mail(subject, message, from_email, recipient_list, fail_silently=False, html_message=notice_html)

        messages.success(request, f'Voiture {voiture.modele} a été affectée au conducteur {conducteur.name}.')
        return redirect('home')
    
    contexts = {
        'voiture': voiture,
        'conducteurs': conducteurs
    }
    return render(request, 'home/affect_voiture.html', contexts)
from typing import Any, Dict, Optional
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy  
from .forms import AddCommentForm
from .models import Lead
from client.models import Client , Comment as  ClinetComment
from team.models import Team
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.views.generic.edit import DeleteView
from django.views import View



class LeadListview(ListView):
    model = Lead
    
    @method_decorator (login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_queryset(self):
        queryset =  super(LeadListview, self).get_queryset()

        return queryset.filter(created_by=self.request.user, converted_to_client=False)
    

class LeadDetailView(DetailView):
    model = Lead

    @method_decorator (login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form']= AddCommentForm()
        return context 
    
    def get_queryset(self):
        queryset =  super(LeadDetailView, self).get_queryset()

        return queryset.filter(created_by=self.request.user, pk=self.kwargs.get('pk'))


class LeadDeleteView(DeleteView):
    model = Lead
    success_url = reverse_lazy('leads:list')
    
    @method_decorator (login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

    def get_queryset(self):
        queryset =  super(LeadDeleteView, self).get_queryset()

        return queryset.filter(created_by=self.request.user, pk=self.kwargs.get('pk'))
    
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
    


class LeadUpdateView(UpdateView):
    model = Lead
    fields = ('name', 'email', 'description', 'priority', 'status',)
    success_url = reverse_lazy('leads:list')

    @method_decorator (login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title']= 'Edit Lead'
        return context     
    
    
    def get_queryset(self):
        queryset =  super(LeadUpdateView, self).get_queryset()

        return queryset.filter(created_by=self.request.user, pk=self.kwargs.get('pk'))

    def form_valid(self, form):
        messages.success(self.request, "Lead has been updated successfully")
        return super().form_valid(form)


class LeadCreateView(CreateView):
    model = Lead
    fields = ('name', 'email', 'description', 'priority', 'status',)
    success_url = reverse_lazy('leads:list')


    @method_decorator (login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = Team.objects.filter(created_by=self.request.user)[0]
        context['team']= team
        context['title']= 'Add Lead'
        return context 
    
    def form_valid(self,form):
        
        team = Team.objects.filter(created_by=self.request.user)[0]

        self.object = form.save(commit=False)
        self.object.created_by= self.request.user
        self.object.team = team 
        self.object.save()

        messages.success(self.request, "Lead has been added to the database succesfully")

        return redirect (self.get_success_url())

class AddCommentView(View):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        form = AddCommentForm(request.POST)

        if form.is_valid():
            team = Team.objects.filter(created_by=request.user)[0]
            comment = form.save(commit=False )
            comment.team = team
            comment.created_by= request.user
            comment.lead_id=pk
            comment.save()

        return redirect('leads:detail', pk=pk  )

class ConvertToClient(View):
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        lead = get_object_or_404(Lead, created_by=request.user, pk=pk)
        team = Team.objects.filter(created_by=request.user)[0]

        client = Client.objects.create(
            name = lead.name,
            email = lead.email,
            description = lead.description,
            created_by = request.user,
            team = team,
        )

    
        lead.converted_to_client = True
        lead.save()

    #convert leads comment to clienr comment
        comments = lead.comments.all()

        for comment in comments:
            ClinetComment.objects.create(
            client = client,
            content = comment.content,
            created_by = comment.created_by,
            team = team, 
        )

        messages.success(request, "Lead has been converted to client succesfully")

        return redirect('leads:list')
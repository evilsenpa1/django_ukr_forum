from django.views.generic import TemplateView

# Create your views here.

class IndexPageView(TemplateView):
    template_name = 'main_temp/index.html'


    def get_context_data(self,**kwargs):
        context =  super().get_context_data(**kwargs)

        num_visits= self.request.session.get('num_visits',0)
        self.request.session['num_visits'] = num_visits +1

        context['num_visits'] = num_visits+1
        return context


class AboutPage(TemplateView):
    template_name = 'main_temp/about.html'

class RulesPage(TemplateView):
    template_name = 'main_temp/rules.html'

class InDevelopmentPage(TemplateView):
    template_name = 'main_temp/in_development.html'
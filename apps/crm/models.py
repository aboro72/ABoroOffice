from django.db import models
from django.conf import settings


class Account(models.Model):
    STATUS_CHOICES = [
        ('active', 'Aktiv'),
        ('inactive', 'Inaktiv'),
        ('prospect', 'Interessent'),
    ]

    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='prospect')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crm_accounts',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Contact(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='contacts')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    title = models.CharField(max_length=100, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crm_contacts',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Lead(models.Model):
    STATUS_CHOICES = [
        ('new', 'Neu'),
        ('contacted', 'Kontaktiert'),
        ('qualified', 'Qualifiziert'),
        ('lost', 'Verloren'),
    ]
    SOURCE_CHOICES = [
        ('web', 'Website'),
        ('email', 'E-Mail'),
        ('phone', 'Telefon'),
        ('event', 'Event'),
        ('referral', 'Empfehlung'),
        ('other', 'Sonstiges'),
    ]

    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='web')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    score = models.IntegerField(default=0)
    rule_score = models.IntegerField(default=0)
    ai_score = models.IntegerField(default=0)
    score_reason = models.TextField(blank=True)
    score_updated_at = models.DateTimeField(null=True, blank=True)
    ai_summary = models.TextField(blank=True)
    ai_next_steps = models.TextField(blank=True)
    ai_followup_subject = models.CharField(max_length=255, blank=True)
    ai_followup_body = models.TextField(blank=True)
    ai_last_question = models.TextField(blank=True)
    ai_last_answer = models.TextField(blank=True)
    ai_last_analyzed = models.DateTimeField(null=True, blank=True)
    ai_status = models.CharField(max_length=20, default='idle')
    ai_error = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crm_leads',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Opportunity(models.Model):
    STAGE_CHOICES = [
        ('prospect', 'Prospect'),
        ('qualified', 'Qualified'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='opportunities')
    name = models.CharField(max_length=255)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='prospect')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    close_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crm_opportunities',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Activity(models.Model):
    TYPE_CHOICES = [
        ('call', 'Anruf'),
        ('email', 'E-Mail'),
        ('meeting', 'Meeting'),
        ('task', 'Aufgabe'),
    ]
    STATUS_CHOICES = [
        ('open', 'Offen'),
        ('done', 'Erledigt'),
        ('cancelled', 'Abgebrochen'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='task')
    subject = models.CharField(max_length=255)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crm_activities',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject


class Note(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name='notes')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='notes')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='notes')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, null=True, blank=True, related_name='notes')
    content = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crm_notes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note {self.id}"


class EmailTemplate(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crm_email_templates',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class EmailLog(models.Model):
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_logs',
    )
    to_email = models.EmailField()
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, default='sent')
    error_message = models.TextField(blank=True)
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_logs',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crm_email_logs',
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Email {self.id}"


class LeadSourceProfile(models.Model):
    SOURCE_CHOICES = [
        ('handelsregister', 'Handelsregister'),
    ]
    KEYWORD_MODE_CHOICES = [
        ('all', 'Alle enthalten'),
        ('min', 'Mindestens ein Schlagwort'),
        ('exact', 'Exakter Firmenname'),
    ]
    SCHEDULE_CHOICES = [
        ('manual', 'Manuell'),
        ('hourly', 'Stündlich'),
        ('daily', 'Täglich'),
        ('weekly', 'Wöchentlich'),
    ]

    name = models.CharField(max_length=200)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='handelsregister')
    keywords = models.CharField(max_length=255, default='IT Beratung')
    keyword_mode = models.CharField(max_length=10, choices=KEYWORD_MODE_CHOICES, default='all')
    search_type = models.CharField(max_length=1, default='n')  # n=normal, e=extended
    results_per_page = models.IntegerField(default=100)
    niederlassung = models.CharField(max_length=200, blank=True)
    register_art = models.CharField(max_length=10, blank=True, default='alle')
    register_nummer = models.CharField(max_length=50, blank=True)
    register_gericht = models.CharField(max_length=50, blank=True)
    rechtsform = models.CharField(max_length=10, blank=True)
    ort = models.CharField(max_length=100, blank=True)
    postleitzahl = models.CharField(max_length=10, blank=True)
    strasse = models.CharField(max_length=200, blank=True)
    suchoptionen_aehnlich = models.BooleanField(default=False)
    suchoptionen_geloescht = models.BooleanField(default=False)
    suchoptionen_nur_zn_neuen_rechts = models.BooleanField(default=False)
    bundesland_bw = models.BooleanField(default=False)
    bundesland_by = models.BooleanField(default=False)
    bundesland_be = models.BooleanField(default=False)
    bundesland_br = models.BooleanField(default=False)
    bundesland_hb = models.BooleanField(default=False)
    bundesland_hh = models.BooleanField(default=False)
    bundesland_he = models.BooleanField(default=False)
    bundesland_mv = models.BooleanField(default=False)
    bundesland_ni = models.BooleanField(default=False)
    bundesland_nw = models.BooleanField(default=False)
    bundesland_rp = models.BooleanField(default=False)
    bundesland_sl = models.BooleanField(default=False)
    bundesland_sn = models.BooleanField(default=False)
    bundesland_st = models.BooleanField(default=False)
    bundesland_sh = models.BooleanField(default=False)
    bundesland_th = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    schedule = models.CharField(max_length=10, choices=SCHEDULE_CHOICES, default='manual')
    max_per_run = models.IntegerField(default=200)
    last_run_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class LeadImportJob(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('rate_limited', 'Rate Limited'),
        ('failed', 'Failed'),
    ]

    profile = models.ForeignKey(LeadSourceProfile, on_delete=models.CASCADE, related_name='jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    requested_count = models.IntegerField(default=0)
    imported_count = models.IntegerField(default=0)
    skipped_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Job {self.id} ({self.profile.name})"


class LeadStaging(models.Model):
    STATUS_CHOICES = [
        ('incomplete', 'Unvollständig'),
        ('ready', 'Bereit'),
        ('imported', 'Importiert'),
        ('skipped', 'Übersprungen'),
        ('needs_website', 'Website gesucht'),
    ]
    ENRICHMENT_CHOICES = [
        ('pending', 'Ausstehend'),
        ('enriched', 'Angereichert'),
        ('no_match', 'Keine Daten'),
        ('error', 'Fehler'),
    ]

    profile = models.ForeignKey(LeadSourceProfile, on_delete=models.CASCADE, related_name='staging_items')
    name = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    source = models.CharField(max_length=100, default='Handelsregister')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='incomplete')
    lead_source = models.CharField(max_length=20, choices=Lead.SOURCE_CHOICES, default='other')
    lead_status = models.CharField(max_length=20, choices=Lead.STATUS_CHOICES, default='new')
    enrichment_status = models.CharField(max_length=20, choices=ENRICHMENT_CHOICES, default='pending')
    enrichment_notes = models.TextField(blank=True)
    enriched_at = models.DateTimeField(null=True, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company


class SourceRequestLog(models.Model):
    source = models.CharField(max_length=50, default='handelsregister')
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source} @ {self.requested_at}"


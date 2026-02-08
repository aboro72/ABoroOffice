from django.views.generic import TemplateView, ListView, DetailView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
import json
from datetime import date
from .models import Project, Task, Milestone, TaskComment
from .forms import ProjectForm, TaskForm, MilestoneForm, TaskCommentForm


def _build_kanban_columns(tasks, limits=None):
    limits = limits or {}
    return [
        ('todo', 'To Do', tasks.filter(status='todo'), limits.get('todo')),
        ('in_progress', 'In Progress', tasks.filter(status='in_progress'), limits.get('in_progress')),
        ('blocked', 'Blocked', tasks.filter(status='blocked'), limits.get('blocked')),
        ('done', 'Done', tasks.filter(status='done'), limits.get('done')),
    ]


def _can_edit(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return user.groups.filter(name='Manager').exists()


def _build_gantt_rows(tasks, milestones=None, extra_ranges=None):
    today = date.today()
    ranges = []
    for task in tasks:
        start = task.project.start_date or task.created_at.date() or today
        end = task.due_date or start
        if end < start:
            end = start
        ranges.append((task, start, end, 'task'))
    if milestones:
        for milestone in milestones:
            start = milestone.due_date or today
            end = start
            ranges.append((milestone, start, end, 'milestone'))
    extra_ranges = extra_ranges or []
    if ranges or extra_ranges:
        min_date = min([r[1] for r in ranges] + [r[0] for r in extra_ranges])
        max_date = max([r[2] for r in ranges] + [r[1] for r in extra_ranges])
    else:
        min_date = today
        max_date = today
    total_days = max(1, (max_date - min_date).days + 1)

    gantt_rows = []
    for item, start, end, kind in ranges:
        offset_days = (start - min_date).days
        duration_days = max(1, (end - start).days + 1)
        left_pct = (offset_days / total_days) * 100
        width_pct = (duration_days / total_days) * 100
        gantt_rows.append({
            'item': item,
            'kind': kind,
            'start': start,
            'end': end,
            'left_pct': left_pct,
            'width_pct': width_pct,
        })
    return gantt_rows, min_date, max_date


class ProjectsHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'projects/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project_count'] = Project.objects.count()
        context['task_count'] = Task.objects.count()
        context['active_projects'] = Project.objects.filter(status='active').count()
        return context


class ProjectsHelpView(LoginRequiredMixin, TemplateView):
    template_name = 'projects/help.html'


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/form.html'
    success_url = reverse_lazy('projects:project_list')


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = self.object.tasks.order_by('-created_at')
        context['tasks'] = tasks
        context['milestones'] = self.object.milestones.order_by('due_date')
        context['task_form'] = TaskForm(initial={'project': self.object})
        context['milestone_form'] = MilestoneForm(initial={'project': self.object})
        context['kanban_columns'] = _build_kanban_columns(tasks, context['wip_limits'])
        gantt_rows, min_date, max_date = _build_gantt_rows(tasks, self.object.milestones.all())
        context['gantt_rows'] = gantt_rows
        context['min_date'] = min_date
        context['max_date'] = max_date
        context['can_edit'] = _can_edit(self.request.user)
        context['wip_limits'] = {
            'todo': self.object.wip_limit_todo,
            'in_progress': self.object.wip_limit_in_progress,
            'blocked': self.object.wip_limit_blocked,
            'done': self.object.wip_limit_done,
        }
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if 'add_task' in request.POST:
            form = TaskForm(request.POST)
            if form.is_valid():
                form.save()
            return redirect('projects:project_detail', pk=self.object.pk)
        if 'add_milestone' in request.POST:
            form = MilestoneForm(request.POST)
            if form.is_valid():
                form.save()
            return redirect('projects:project_detail', pk=self.object.pk)
        return redirect('projects:project_detail', pk=self.object.pk)


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'projects/task_list.html'
    context_object_name = 'tasks'


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'projects/form.html'
    success_url = reverse_lazy('projects:task_list')


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'projects/task_detail.html'
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.order_by('-created_at')
        context['comment_form'] = TaskCommentForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if 'add_comment' in request.POST:
            form = TaskCommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.task = self.object
                comment.author = request.user
                comment.created_at = timezone.now()
                comment.save()
        return redirect('projects:task_detail', pk=self.object.pk)


class TaskStatusUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not _can_edit(request.user):
            return JsonResponse({'ok': False, 'error': 'permission denied'}, status=403)
        status = request.POST.get('status')
        if status not in dict(Task.STATUS_CHOICES):
            return JsonResponse({'ok': False, 'error': 'invalid status'}, status=400)
        task = Task.objects.filter(pk=pk).first()
        if not task:
            return JsonResponse({'ok': False, 'error': 'not found'}, status=404)
        limits = {
            'todo': task.project.wip_limit_todo,
            'in_progress': task.project.wip_limit_in_progress,
            'blocked': task.project.wip_limit_blocked,
            'done': task.project.wip_limit_done,
        }
        limit = limits.get(status)
        if limit is not None:
            current = Task.objects.filter(project=task.project, status=status).exclude(pk=task.pk).count()
            if current >= limit:
                return JsonResponse({'ok': False, 'error': f'WIP-Limit erreicht ({limit})'}, status=400)
        if task.project.wip_limit_assignee is not None and task.assignee_id:
            current_assignee = Task.objects.filter(
                project=task.project,
                assignee_id=task.assignee_id,
                status='in_progress',
            ).exclude(pk=task.pk).count()
            if current_assignee >= task.project.wip_limit_assignee and status == 'in_progress':
                return JsonResponse({'ok': False, 'error': f'Assignee WIP-Limit erreicht ({task.project.wip_limit_assignee})'}, status=400)
        if task.project.wip_limit_team is not None and task.assignee_id and status == 'in_progress':
            group = task.assignee.groups.first()
            if group:
                current_team = Task.objects.filter(
                    project=task.project,
                    assignee__groups=group,
                    status='in_progress',
                ).exclude(pk=task.pk).count()
                if current_team >= task.project.wip_limit_team:
                    return JsonResponse({'ok': False, 'error': f'Team WIP-Limit erreicht ({task.project.wip_limit_team})'}, status=400)
        task.status = status
        task.save(update_fields=['status'])
        return JsonResponse({'ok': True, 'status': status})


class KanbanView(LoginRequiredMixin, TemplateView):
    template_name = 'projects/kanban.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.request.GET.get('project')
        lane = self.request.GET.get('lane', 'none')
        assignee_id = self.request.GET.get('assignee')
        tasks = Task.objects.select_related('project', 'assignee')
        if project_id:
            tasks = tasks.filter(project_id=project_id)
        if assignee_id and assignee_id.isdigit():
            tasks = tasks.filter(assignee_id=int(assignee_id))
        context['projects'] = Project.objects.order_by('name')
        context['selected_project'] = int(project_id) if project_id and project_id.isdigit() else None
        context['selected_lane'] = lane
        context['selected_assignee'] = int(assignee_id) if assignee_id and assignee_id.isdigit() else None
        context['assignees'] = (
            tasks.exclude(assignee__isnull=True)
            .values_list('assignee__id', 'assignee__username')
            .distinct()
        )
        context['can_edit'] = _can_edit(self.request.user)
        context['project_limits'] = {}
        if project_id and project_id.isdigit():
            project = Project.objects.filter(id=int(project_id)).first()
            if project:
                context['project_limits'] = {
                    'todo': project.wip_limit_todo,
                    'in_progress': project.wip_limit_in_progress,
                    'blocked': project.wip_limit_blocked,
                    'done': project.wip_limit_done,
                    'wip_limit_assignee': project.wip_limit_assignee,
                    'wip_limit_team': project.wip_limit_team,
                }
        if lane == 'project':
            lanes = []
            for p in Project.objects.order_by('name'):
                lane_tasks = tasks.filter(project=p)
                lanes.append({
                    'title': p.name,
                    'columns': _build_kanban_columns(lane_tasks, {
                        'todo': p.wip_limit_todo,
                        'in_progress': p.wip_limit_in_progress,
                        'blocked': p.wip_limit_blocked,
                        'done': p.wip_limit_done,
                    }),
                    'limits': {
                        'todo': p.wip_limit_todo,
                        'in_progress': p.wip_limit_in_progress,
                        'blocked': p.wip_limit_blocked,
                        'done': p.wip_limit_done,
                    },
                })
            context['lanes'] = lanes
        elif lane == 'assignee':
            lanes = []
            for uid, uname in context['assignees']:
                lane_tasks = tasks.filter(assignee_id=uid)
                lanes.append({'title': uname or 'Unassigned', 'columns': _build_kanban_columns(lane_tasks)})
            context['lanes'] = lanes
        else:
            context['columns'] = _build_kanban_columns(tasks, context['project_limits'])
        return context


class GanttView(LoginRequiredMixin, TemplateView):
    template_name = 'projects/gantt.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.request.GET.get('project')
        zoom = self.request.GET.get('zoom', 'month')
        tasks = Task.objects.select_related('project', 'assignee')
        milestones = Milestone.objects.select_related('project')
        projects = Project.objects.all()
        if project_id:
            tasks = tasks.filter(project_id=project_id)
            milestones = milestones.filter(project_id=project_id)
            projects = projects.filter(id=project_id)
        tasks = tasks.order_by('due_date', 'created_at')
        context['projects'] = Project.objects.order_by('name')
        context['selected_project'] = int(project_id) if project_id and project_id.isdigit() else None
        context['selected_zoom'] = zoom
        project_ranges = []
        for p in projects:
            if p.start_date and p.due_date:
                project_ranges.append((p.start_date, p.due_date, p))
        gantt_rows, min_date, max_date = _build_gantt_rows(
            tasks,
            milestones,
            extra_ranges=[(r[0], r[1]) for r in project_ranges],
        )
        context['gantt_rows'] = gantt_rows
        context['min_date'] = min_date
        context['max_date'] = max_date
        project_rows = []
        total_days = max(1, (max_date - min_date).days + 1)
        for start, end, project in project_ranges:
            offset_days = (start - min_date).days
            duration_days = max(1, (end - start).days + 1)
            project_rows.append({
                'project': project,
                'start': start,
                'end': end,
                'left_pct': (offset_days / total_days) * 100,
                'width_pct': (duration_days / total_days) * 100,
            })
        context['project_rows'] = project_rows
        # timeline ticks
        ticks = []
        if zoom == 'week':
            step = 7
        elif zoom == 'day':
            step = 1
        else:
            step = 30
        total_days = max(1, (max_date - min_date).days + 1)
        day = 0
        while day <= total_days:
            left = (day / total_days) * 100
            ticks.append({'left': left, 'day': day})
            day += step
        context['ticks'] = ticks
        return context


class GanttExportView(LoginRequiredMixin, View):
    def get(self, request):
        project_id = request.GET.get('project')
        export_format = request.GET.get('format', 'csv')
        tasks = Task.objects.select_related('project')
        milestones = Milestone.objects.select_related('project')
        projects = Project.objects.all()
        if project_id and project_id.isdigit():
            tasks = tasks.filter(project_id=project_id)
            milestones = milestones.filter(project_id=project_id)
            projects = projects.filter(id=project_id)
        rows = []
        for task in tasks:
            rows.append(['task', task.project.name, task.title, str(task.due_date or '')])
        for ms in milestones:
            rows.append(['milestone', ms.project.name, ms.title, str(ms.due_date or '')])
        if export_format == 'pdf':
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            resp = HttpResponse(content_type='application/pdf')
            resp['Content-Disposition'] = 'attachment; filename=\"gantt_export.pdf\"'
            c = canvas.Canvas(resp, pagesize=A4)
            width, height = A4
            y = height - 40
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "Gantt Export (Balken)")
            y -= 20

            project_ranges = []
            for p in projects:
                if p.start_date and p.due_date:
                    project_ranges.append((p.start_date, p.due_date, p.name))
            gantt_rows, min_date, max_date = _build_gantt_rows(tasks, milestones, extra_ranges=[(r[0], r[1]) for r in project_ranges])
            total_days = max(1, (max_date - min_date).days + 1)
            chart_left = 180
            chart_width = width - chart_left - 40

            c.setFont("Helvetica-Bold", 10)
            c.drawString(40, y, "Projekt-Zeitleiste")
            y -= 14
            c.setFont("Helvetica", 9)
            # grid
            c.setStrokeColorRGB(0.9, 0.9, 0.9)
            for d in range(0, total_days + 1, 7):
                x = chart_left + (d / total_days) * chart_width
                c.line(x, y - 6, x, y - 6 - (len(project_ranges) + len(gantt_rows) + 6) * 12)
            c.setStrokeColorRGB(0, 0, 0)
            for start, end, name in project_ranges:
                if y < 60:
                    c.showPage()
                    y = height - 40
                offset = (start - min_date).days
                duration = max(1, (end - start).days + 1)
                left = chart_left + (offset / total_days) * chart_width
                bar_w = (duration / total_days) * chart_width
                c.drawString(40, y, name[:25])
                c.setFillColorRGB(0.2, 0.6, 0.2)
                c.rect(left, y - 3, max(2, bar_w), 6, fill=1, stroke=0)
                c.setFillColorRGB(0, 0, 0)
                y -= 12

            y -= 6
            c.setFont("Helvetica-Bold", 10)
            c.drawString(40, y, "Tasks & Meilensteine")
            y -= 14
            c.setFont("Helvetica", 9)
            for row in gantt_rows:
                if y < 60:
                    c.showPage()
                    y = height - 40
                label = row['item'].title[:25]
                offset = (row['start'] - min_date).days
                duration = max(1, (row['end'] - row['start']).days + 1)
                left = chart_left + (offset / total_days) * chart_width
                bar_w = (duration / total_days) * chart_width
                c.drawString(40, y, label)
                if row['kind'] == 'milestone':
                    c.setFillColorRGB(1, 0.7, 0.1)
                    c.rect(left, y - 3, 4, 6, fill=1, stroke=0)
                else:
                    c.setFillColorRGB(0.2, 0.4, 0.9)
                    c.rect(left, y - 3, max(2, bar_w), 6, fill=1, stroke=0)
                c.setFillColorRGB(0, 0, 0)
                y -= 12
            # legend
            y -= 6
            c.setFont("Helvetica-Bold", 9)
            c.drawString(40, y, "Legende:")
            c.setFont("Helvetica", 9)
            c.setFillColorRGB(0.2, 0.6, 0.2)
            c.rect(90, y - 4, 10, 6, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(105, y - 2, "Projekt")
            c.setFillColorRGB(0.2, 0.4, 0.9)
            c.rect(150, y - 4, 10, 6, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(165, y - 2, "Task")
            c.setFillColorRGB(1, 0.7, 0.1)
            c.rect(205, y - 4, 6, 6, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(218, y - 2, "Meilenstein")
            c.save()
            return resp
        csv_lines = ["type,project,title,due_date"]
        for r in rows:
            csv_lines.append(",".join([str(x).replace(',', ' ') for x in r]))
        resp = HttpResponse("\n".join(csv_lines), content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename=\"gantt_export.csv\"'
        return resp

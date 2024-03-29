from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    post_list = Post.objects.all()

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get(
        'page')
    page = paginator.get_page(
        page_number)

    return render(request, 'index.html',
                  {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'posts/group.html',
                  {'group': group,
                   'page': page,
                   'paginator': paginator})


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None,
                        files=request.FILES or None)

        if form.is_valid():
            post_new = form.save(commit=False)
            post_new.author = request.user
            post_new.save()
            return redirect('index')

        return render(request, 'posts/new-post.html', {'form': form})

    form = PostForm()
    return render(request, 'posts/new-post.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            author=author,
            user=request.user
        ).exists()

    return render(request, 'posts/profile.html',
                  {'author': author,
                   'page': page,
                   'paginator': paginator,
                   'following': following})


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.posts, id=post_id)
    comments = post.comments.all()
    form = CommentForm()

    return render(request, 'posts/post.html',
                  {'post': post,
                   'author': author,
                   'form': form,
                   'items': comments})


@login_required
def post_edit(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.posts, id=post_id)

    if author != request.user:
        return redirect('post_view', username, post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('post_view', username, post_id)

        return render(request, 'posts/new_post.html',
                      {'form': form,
                       'author': author,
                       'post': post})



@login_required
def add_comment(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.posts, id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)

        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.author = request.user
            new_comment.post = post
            new_comment.save()

    return redirect('post_view', username=username, post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'posts/follow.html',
                  {'page': page,
                   'paginator': paginator})


@require_http_methods(["GET"])
@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)

    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)

    return redirect('profile', username=username)


@require_http_methods(["GET"])
@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)

    if request.user != author:
        Follow.objects.filter(user=request.user, author=author).delete()

    return redirect('profile', username)


def page_not_found(request, exception):
        return render(request, 'misc/404.html',
                      {"path": request.path},
                      status=404)


def server_error(request):
    return render(request,
                  'misc/500.html',
                  status=500)

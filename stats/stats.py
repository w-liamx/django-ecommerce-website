from products.models import Item
from .models import ItemView
from search.models import SearchTerm
from cstore.utils import random_string_generator
from cstore.settings import PRODUCTS_PER_ROW


def tracking_id(request):
    track_id = request.session.get('tracking_id', None)
    if track_id == None:
        track_id = request.session['tracking_id'] = random_string_generator(
            size=30)
    return track_id


def log_item_view(request, item):
    t_id = tracking_id(request)
    try:
        v = ItemView.objects.get(tracking_id=t_id, item=item)
    except ItemView.DoesNotExist:
        v = ItemView.objects.create(
            ip_address=request.META.get('REMOTE_ADDR'),
            tracking_id=t_id,
            item=item,
            user=None
        )
        if request.user.is_authenticated:
            v.user = request.user
        v.save()


def recommended_from_views(request):
    t_id = tracking_id(request)
    viewed = get_recently_viewed()
    if viewed:
        itemviews = ItemView.objects.filter(
            item__in=viewed).values('tracking_id')
        t_ids = [v['tracking_id'] for v in itemviews]
        if t_ids:
            all_viewed = Item.objects.all().filter(itemview__tracking_id__in=t_ids)
            if all_viewed:
                other_viewed = ItemView.objects.filter(
                    item__in=all_viewed).exclude(item__in=viewed)
                if other_viewed:
                    return Item.objects.all().filter(itemview__in=other_viewed).distinct()


def get_recently_viewed(request):
    t_id = tracking_id(request)
    views = ItemView.objects.filter(tracking_id=t_id).values(
        'item_id').order_by('-date')[0:4]
    item_ids = [v['item_id'] for v in views]
    return Item.objects.all().filter(id__in=item_ids)


def recommended_from_search(request):
    # get common words from stored searches
    common_words = frequently_searched_words(request)
    from search.filter import search_words
    matching = []
    for word in common_words:
        results = search_words(value=word, queryset=Item.objects.all())
        for r in results:
            if len(matching) < PRODUCTS_PER_ROW and not r in matching:
                matching.append(r)
    return matching


def frequently_searched_words(request):
    # get the first 10 most recent searches from the database.
    searches = SearchTerm.objects.filter(tracking_id=tracking_id(
        request)).values('query').order_by('-search_date')[0:10]
    # join all searches together to one string
    search_string = ''.join([search['query'] for search in searches])
    # return the top 3 most common words in the searches
    return sort_words_by_frequency(search_string)[0:3]


def sort_words_by_frequency(the_string):
    # convert string to python list
    words = the_string.split()
    # rank the words based on frequency
    ranked_words = [[word, words.count(word)] for word in set(words)]
    # sort words in descending order
    sorted_words = sorted(ranked_words, key=lambda word: -word[1])
    # return the list of words according to ranking
    return [i[0] for i in sorted_words]

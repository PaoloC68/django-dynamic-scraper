import os.path

from django.test import TestCase

from scrapy import signals
from scrapy.conf import settings
from scrapy.crawler import CrawlerProcess
from scrapy.xlib.pydispatch import dispatcher

from dynamic_scraper.spiders.django_spider import DjangoSpider
from dynamic_scraper.spiders.django_checker import DjangoChecker
from dynamic_scraper.models import *
from scraper.models import EventWebsite, Event, EventItem


# Tests need webserver for serving test pages: python manage.py runserver 0.0.0.0:8010


class EventSpider(DjangoSpider):
    
    name = 'event_spider'

    def __init__(self, *args, **kwargs):
        self._set_ref_object(EventWebsite, **kwargs)
        self.scraper = self.ref_object.scraper
        self.scraper_runtime = self.ref_object.scraper_runtime
        self.scraped_obj_class = Event
        self.scraped_obj_item_class = EventItem
        self._set_start_urls(self.ref_object.url)
        super(EventSpider, self).__init__(self, *args, **kwargs)


class DjangoWriterPipeline(object):
    
    def process_item(self, item, spider):
        item['event_website'] = spider.ref_object
        item.save()
        return item 


class EventChecker(DjangoChecker):
    
    name = 'event_checker'
    
    def __init__(self, *args, **kwargs):
        self._set_ref_object(Event, **kwargs)
        self.scraper = self.ref_object.event_website.scraper
        self.scheduler_runtime = self.ref_object.checker_runtime
        self.check_url = self.ref_object.url
        super(EventChecker, self).__init__(self, *args, **kwargs)


class ScraperTest(TestCase):

    SERVER_URL = 'http://localhost:8010/static/'
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
    

    def record_signal(self, *args, **kwargs):
        pass
        #print kwargs
    

    def run_event_spider(self, id):
        kwargs = {
        'id': id,
        'do_action': 'yes'
        }
        spider = EventSpider(**kwargs)
        self.crawler.crawl(spider)
        self.crawler.start()
        
    
    def run_event_checker(self, id):
        kwargs = {
        'id': id,
        'do_action': 'yes'
        }
        checker = EventChecker(**kwargs)
        self.crawler.crawl(checker)
        self.crawler.start()

    
    def setUp(self):        
        self.sc = ScrapedObjClass(name='Event')
        self.sc.save()
        self.soa_base = ScrapedObjAttr(name=u'base', attr_type='B', obj_class=self.sc)
        self.soa_base.save()
        self.soa_title = ScrapedObjAttr(name=u'title', attr_type='S', obj_class=self.sc)
        self.soa_title.save()
        self.soa_url = ScrapedObjAttr(name=u'url', attr_type='U', obj_class=self.sc)
        self.soa_url.save()
        self.soa_desc = ScrapedObjAttr(name=u'description', attr_type='S', obj_class=self.sc)
        self.soa_desc.save()

        self.scraper = Scraper(name=u'Event Scraper', scraped_obj_class=self.sc)
        self.scraper.save()
        
        self.se_base = ScraperElem(scraped_obj_attr=self.soa_base, scraper=self.scraper, 
        x_path=u'//ul/li', follow_url=False)
        self.se_base.save()
        self.se_title = ScraperElem(scraped_obj_attr=self.soa_title, scraper=self.scraper, 
            x_path=u'a/text()', follow_url=False)
        self.se_title.save()
        self.se_url = ScraperElem(scraped_obj_attr=self.soa_url, scraper=self.scraper, 
            x_path=u'a/@href', follow_url=False)
        self.se_url.save()
        self.se_desc = ScraperElem(scraped_obj_attr=self.soa_desc, scraper=self.scraper, 
            x_path=u'//div/div[@class="description"]/text()', follow_url=True, mandatory=False)
        self.se_desc.save()
        
        self.sched_rt = SchedulerRuntime()
        self.sched_rt.save()
        
        self.scraper_rt = ScraperRuntime(name=u'Events Runtime', scheduler_runtime=self.sched_rt)
        self.scraper_rt.save()
        
        self.event_website = EventWebsite(pk=1, name=u'Event Website', url=os.path.join(self.SERVER_URL, 'site_generic/event_main.html'),
            scraper=self.scraper, scraper_runtime=self.scraper_rt)
        self.event_website.save()
        
        
        settings.overrides['ITEM_PIPELINES'] = [
            'dynamic_scraper.pipelines.DjangoImagesPipeline',
            'dynamic_scraper.pipelines.ValidationPipeline',
            'scraper.scraper_test.DjangoWriterPipeline',
        ]
        
        settings.overrides['IMAGES_STORE'] = os.path.join(self.PROJECT_ROOT, 'imgs')
        settings.overrides['IMAGES_THUMBS'] = { 'small': (170, 170), }
        
        self.crawler = CrawlerProcess(settings)
        self.crawler.install()
        self.crawler.configure()
        
        for name, signal in vars(signals).items():
            if not name.startswith('_'):
                dispatcher.connect(self.record_signal, signal)
        
    
    def tearDown(self):
        pass
        

        
    
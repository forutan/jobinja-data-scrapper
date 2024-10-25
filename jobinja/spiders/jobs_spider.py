import scrapy
import scrapy.http
import re

def remove_space(s):
    return replace_multiple_spaces(s.strip(' \n'))

def replace_multiple_spaces(text):
    return re.sub(r'\s+', ' ', text)

class JobSpider(scrapy.Spider):
    name = "jobs"
    allowed_domains = ["jobinja.ir"]

    def start_requests(self):
        urls = [
            "https://jobinja.ir/jobs?page=1",
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response: scrapy.http.Response):

        jobs = response.css(".o-listView__list .o-listView__item")

        for job in jobs:
            title_text = job.css(".c-jobListView__titleLink::text").get()
            meta = job.css(".c-jobListView__metaItem span::text").getall()
            passed_days = job.css(".c-jobListView__passedDays::text").get()
            is_premium = job.css(".c-jobListView__item--premium .c-jobListView__titleLink").get()

            meta_list = list(filter(None, map(remove_space, meta)))
            meta_list_len = len(meta_list)

            item = {
                "title": remove_space(title_text),
                "meta_1": meta_list[0] if meta_list_len > 0 else None,
                "meta_2": meta_list[1] if meta_list_len > 1 else None,
                "meta_3": meta_list[2] if meta_list_len > 2 else None,
                "passed_days": passed_days.strip(),
                "is_premium": bool(is_premium)
            }

            title = job.css(".c-jobListView__titleLink::attr(href)").get()
            yield response.follow(title, callback=self.parse_extra_info, meta={'item': item})


        next_page = response.css('.paginator a[rel="next"]::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)
    
    def parse_extra_info(self, response):
        item = response.meta['item']
        info_box_items = response.css(".c-infoBox__item")


        for info_box in info_box_items:
            info_title = info_box.css(".c-infoBox__itemTitle::text").get()
            tags = info_box.css(".tags span::text").getall()
            item[info_title] = list(map(lambda s: remove_space(s), tags))

        
        description_title = response.xpath("//*[contains(@class, 'o-box__title')]")

        for desc in description_title:
            title = desc.xpath('./text()').get()
            content = desc.xpath('following-sibling::div//text()').getall()
            item[title] = remove_space(' '.join(content).strip())

        comapny_meta_raw = response.xpath("//*[contains(@class, 'c-companyHeader__metaItem')]//text()").getall()
        comapny_meta = list(filter(None, map(lambda s: remove_space(s), comapny_meta_raw)))

        # comapny_meta_len = len(comapny_meta)
        
        # item['company_meta_1'] = comapny_meta[0] if comapny_meta_len > 0 else None
        # item['company_meta_2'] = comapny_meta[1] if comapny_meta_len > 1 else None
        # item['company_meta_3'] =  comapny_meta[2] if comapny_meta_len > 2 else None
        # item['company_meta_4'] = comapny_meta[3] if comapny_meta_len > 3 else None
        # item['company_meta_5'] = comapny_meta[4] if comapny_meta_len > 4 else None

        item['company_meta'] = comapny_meta

        yield item
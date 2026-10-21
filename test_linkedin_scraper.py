import unittest
from linkedin_scraper import Page, cards, detail, job_id


class ParsingTests(unittest.TestCase):
    def test_job_ids(self):
        self.assertEqual(job_id('https://br.linkedin.com/jobs/view/analista-at-company-123456?x=1'), '123456')
        self.assertEqual(job_id('https://www.linkedin.com/jobs/view/123456/'), '123456')
        self.assertIsNone(job_id('https://www.linkedin.com/jobs/search/'))

    def test_cards_deduplicate_and_decode(self):
        card = '''<div class="base-card"><a class="base-card__full-link"
          href="https://www.linkedin.com/jobs/view/test-123456?tracking=x"></a>
          <h3 class="base-search-card__title">Dados &amp; Pesquisa</h3>
          <h4 class="base-search-card__subtitle">Empresa</h4>
          <span class="job-search-card__location">Brasil</span>
          <time datetime="2026-10-19"></time></div>'''
        rows = cards(Page('<div class>' + card + card + '</div>').root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Title'], 'Dados & Pesquisa')
        self.assertEqual(rows[0]['Date'], '2026-10-19')

    def test_description_cannot_be_attached_to_wrong_job(self):
        html = '''<link rel="canonical" href="https://www.linkedin.com/jobs/view/123456/">
          <h1>Analista de Dados</h1><div class="show-more-less-html__markup">'''
        html += 'Analisar dados e preparar relatórios. ' * 5 + '</div>'
        page = Page(html).root
        self.assertTrue(detail(page, {'ID': '123456'})['Description'])
        with self.assertRaises(ValueError):
            detail(page, {'ID': '999999'})

    def test_missing_description_is_not_success(self):
        page = Page('<link rel="canonical" href="https://www.linkedin.com/jobs/view/123456/"><h1>Analista</h1>').root
        with self.assertRaises(ValueError):
            detail(page, {'ID': '123456'})


if __name__ == '__main__':
    unittest.main()

import builtins

from ingest.scrapers.integrate import integrate_scraped_item


def test_integrate_scraped_item_calls_store(monkeypatch):
    called = {}

    def fake_store(md_text, context, assets, src_path, out_dir):
        called['md_text'] = md_text
        called['context'] = context
        called['assets'] = assets
        called['src_path'] = src_path
        called['out_dir'] = out_dir
        return ('out/sample.md', 'out/sample.json')

    # Patch the symbol imported into the integrate module
    monkeypatch.setattr('ingest.scrapers.integrate.store_conversion', fake_store)

    sample = {
        'title': 'Sample Event',
        'summary': 'This is a sample event.',
        'date': '2026-04-01',
        'location': 'Online',
        'source_url': 'https://example.org/events/1'
    }

    md_path, json_path = integrate_scraped_item(sample, 'example-org', out_dir='out')
    assert md_path == 'out/sample.md'
    assert json_path == 'out/sample.json'
    assert 'Sample Event' in called['md_text']
    assert called['context']['source'] == 'external'
    assert called['src_path'] == sample['source_url']

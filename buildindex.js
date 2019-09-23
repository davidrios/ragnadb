const fs = require('fs')

const lunr = require('lunr')
const sanitizeHtml = require('sanitize-html')

if (process.argv.length !== 4) {
  console.error('Usage: buildindex DB_FILE OUT_FILE')
  process.exit()
}

const db = JSON.parse(fs.readFileSync(process.argv[2], { encoding: 'utf8' }))

const idx = lunr(function () {
  this.ref('id')
  this.field('name')
  this.field('text')

  for (const iid in db.items) {
    const item = db.items[iid]
    this.add({ id: item.id, name: item.name, text: sanitizeHtml(item.text, { allowedTags: [] }) })
  }
})

fs.writeFileSync(process.argv[3], JSON.stringify(idx), { encoding: 'utf8' })

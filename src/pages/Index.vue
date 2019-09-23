<template>
  <q-page class="main">
    <p class="error" v-if="errorMessage">{{ errorMessage }}</p>
    <q-table
      v-if="!errorMessage"
      title="Itens"
      :data="itemsList"
      :columns="itemsColumns"
      row-key="id"
      >
      <template v-slot:body-cell-sprite="props">
        <q-td :props="props">
          <div class="sprite-container flex flex-center">
            <img :src="`/data/images/sprite/${props.value}.png`" />
          </div>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<style>
  .main {
    padding: 3em;
  }

  p.error {
    text-align: center;
    font-size: 2em;
    color: red;
  }

  div.sprite-container {
    background-color: #dddddd;
    padding: 2px;
    width: 30px;
    height: 30px;
    border-radius: 5px;
  }
</style>

<script>
import lunr from 'lunr'
import PouchDB from 'pouchdb'
import pouchdbFind from 'pouchdb-find'

PouchDB.plugin(pouchdbFind)

export default {
  name: 'PageIndex',
  data () {
    return {
      itemsList: [],
      itemsColumns: [
        {
          field: 'sprite',
          name: 'sprite',
          align: 'left'
        },
        {
          field: 'id',
          name: 'id',
          label: 'ID Item',
          align: 'left',
          sortable: true,
          sort: (a, b) => parseFloat(a, 10) - parseFloat(b, 10)
        },
        {
          field: 'name',
          name: 'name',
          label: 'Nome',
          align: 'left',
          sortable: true,
          sort: (a, b) => a.localeCompare(b)
        },
        {
          field: 'minimumLevel',
          name: 'minimumLevel',
          label: 'Nível necessário',
          align: 'right',
          sortable: true,
          sort: (a, b) => parseFloat(a, 10) - parseFloat(b, 10)
        },
        {
          field: 'attack',
          name: 'attack',
          label: 'Ataque',
          align: 'right',
          sortable: true,
          sort: (a, b) => parseFloat(a, 10) - parseFloat(b, 10)
        },
        {
          field: 'defense',
          name: 'defense',
          label: 'Defesa',
          align: 'right',
          sortable: true,
          sort: (a, b) => parseFloat(a, 10) - parseFloat(b, 10)
        },
        {
          field: 'weight',
          name: 'weight',
          label: 'Peso',
          align: 'right',
          sortable: true,
          sort: (a, b) => parseFloat(a, 10) - parseFloat(b, 10)
        }
      ],
      rawDb: null,
      db: null,
      lunrIndex: null,
      errorMessage: null
    }
  },
  mounted () {
    this.$q.loading.show()
    this.loadData()
  },
  methods: {
    loadData () {
      Promise.all(
        [
          fetch('/data/db.json'),
          fetch('/data/index.json')
        ]
      ).then((values) => {
        for (const res of values) {
          if (!res.ok) {
            this.$q.loading.hide()
            this.errorMessage = 'Error loading data.'
            return
          }
        }

        Promise.all(values.map(res => res.json())).then((values) => {
          this.rawDb = values[0]
          this.lunrIndex = lunr.Index.load(values[1])
          this.db = new PouchDB('items')

          this.db.destroy().then(() => {
            this.db = new PouchDB('items')

            this.db.bulkDocs(Object.values(this.rawDb.items)).then(() => {
              // this.db.createIndex({
              //   index: {
              //     fields: ['name', ...Object.keys(this.rawDb.metaprops).map(item => 'props.' + item)]
              //   }
              // }).then(() => {
              this.$q.loading.hide()
              // })
            })

            window.db = this.db
          })

          const newItems = []

          for (const iid in this.rawDb.items) {
            const item = this.rawDb.items[iid]
            if (parseInt(iid) > 2000) {
              continue
            }

            newItems.push({
              sprite: item.res,
              id: item.id,
              name: item.name,
              attack: item.props ? item.props.attack : null,
              defense: item.props ? item.props.defense : null,
              minimumLevel: item.props ? item.props.minimumLevel || '1' : null,
              weight: item.props ? item.props.weigth : null
            })
          }

          this.itemsList = newItems

          window.rawDb = this.rawDb
          window.lunrIndex = this.lunrIndex
        })
      })
    }
  }
}
</script>

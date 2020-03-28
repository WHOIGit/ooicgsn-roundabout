/*
# Copyright (C) 2019-2020 Woods Hole Oceanographic Institution
#
# This file is part of the Roundabout Database project ("RDB" or
# "ooicgsn-roundabout").
#
# ooicgsn-roundabout is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# ooicgsn-roundabout is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ooicgsn-roundabout in the COPYING.md file at the project root.
# If not, see <http://www.gnu.org/licenses/>.
*/

function str2html(html_string) {
    const template = document.createElement('template');
    template.innerHTML = html_string;
    if (template.content.childNodes.length===1){
          return template.content.firstChild
    }else{return template.content.childNodes}
}
String.prototype.replaceAll = function(search, replacement) {
    const target = this
    return target.split(search).join(replacement)
};


function create_card(card_name,type,rows_data=null){

    var card_html = `<div class="card qcard" id="qcard_c{{ cindex }}">{{ card_header }}{{ card_body }}</div>`

    var card_header = `
  <div class="card-header form-group form-inline">
    <!--<input type="hidden" value="{{ type }}" name="m{{ cindex }}">-->
  </div>`.replace('{{ type }}',type)

    if (type === 'inventory'){
        card_header = card_header.replace('value="inventory"','value="inventory" selected')}
    else if (type === 'part'){
        card_header = card_header.replace('value="part"','value="part" selected')}
    else if (type === 'builds'){
        card_header = card_header.replace('value="builds"','value="builds" selected')}
    else if (type === 'assembly'){
        card_header = card_header.replace('value="assembly"','value="assembly" selected')}


    var card_body = `
      <div class="card-body">
        <div id="fields_c{{ cindex }}">
          {{ card_rows }}
        </div>
        {{ plus_button }}
      </div>`

    let card_rows = ''
    if (rows_data){
        for (let row_idx in rows_data){
            card_rows = card_rows+create_row(card_name,type,row_idx,rows_data[row_idx])
          }
    }
    else{
        card_rows = create_row(card_name,type,0)
    }

    var plus_button = `<button type='button' class="btn btn-primary-sm" id="qfield_+AND_c{{ cindex }}" href="#"
                      onclick="insert_row(card_idx='{{ cindex }}',type='{{ type }}');return false;" >
                      <i class="fa fa-plus"></i> AND</button>`.replace('{{ type }}',type)
    card_body = card_body.replace('{{ card_rows }}',card_rows).replace('{{ plus_button }}',plus_button)
    card_html = card_html.replace('{{ card_header }}', card_header).replace('{{ card_body }}', card_body)
    card_html = card_html.replaceAll('{{ cindex }}',card_name)
    return card_html
}

function insert_card(type,rows_data=null){
    var cards = document.getElementById('adv-search-cards')
    var name = cards.children.length
    var new_card = str2html(create_card(name,type,rows_data))
    cards.appendChild(new_card)
}
function replace_card(name){ // DEPRICATED
    var card_id = 'qcard_c{{ cindex }}'.replace('{{ cindex }}',name)
    var card = document.getElementById(card_id)
    //var type_selector_id = 'model-select_c{{ cindex }}'.replace('{{ cindex }}',name)
    //var type_selector = document.getElementById(type_selector_id)
    var type = '{{ model }}' //$("#model-select").value
    var new_card = str2html(create_card(name,type))
    card.parentNode.replaceChild(new_card, card)
}
function replace_cards(selectObj){
    $("#adv-search-cards").empty()
    const card_type = selectObj.value //$("#model-select")
    insert_card(card_type)

    //var cards = document.getElementsByClassName('qcard')

}

function create_row(card_idx, type, row_index,row_data=null){
    let init_fields = []
    let init_lookup = 'icontains'
    let init_query = ''
    if (row_data){
        init_fields =  row_data['fields']
        init_lookup = row_data['lookup']
        init_query = row_data['query']
    }
    else{
        if (type === 'inventory'){      init_fields = []    }
        else if (type === 'part'){      init_fields = []            }
        else if (type === 'builds'){    init_fields = []     }
        else if (type === 'assembly'){  init_fields = []  }
    }

    const row_id = "qfield-row_c{{ cindex }}_f{{ findex }}"
    let row = `<div id="{{ row_id }}" class="form-group form-inline">
                 <select size='7' class="selectpicker form-control col-md-4" multiple id="field-select_c{{ cindex }}_f{{ findex }}" name="m{{ cindex }}_f{{ findex }}">{{ options }}</select>{{ lookup }}{{ query }}{{ minus_button }}</div>`
    row = row.replace("{{ row_id }}",row_id)
    let options = ''
    if (type === 'inventory'){
        options = `<option value="part__name">Name</option>
                   <option value="serial_number">Serial Number</option>
                   <option value="build__assembly__name">Build</option>
                   <option value="revision__note">Note</option>
                   <option value="created_at">Date Created</option>
                   <option value="updated_at">Date Modified</option>

                   <option disabled style="font-style:italic">--Part--</option>
                   <option value="part__part_type__name">Part Type</option>
                   <option value="part__unit_cost">Unit Cost</option>
                   <option value="part__refurbishment_cost">Refurb Cost</option>

                   <option disabled style="font-style:italic">--Location--</option>
                   <option value="location__name">Name</option>
                   <option value="location__location_type">Type</option>
                   <option value="location__root_type">Root</option>
                   <option disabled style="font-style:italic">--User-Defined-Fields--</option>
                   <option value="fieldvalues__field__field_name">UDF Name</option>
                   <option value="fieldvalues__field_value">UDF Value</option>`
    }

    else if (type === 'part'){
        options = `<option value="part_number">Part Number</option>
                   <option value="name">Name</option>
                   <option value="part_type__name">Part Type</option>
                   <option value="unit_cost">Unit Cost</option>
                   <option value="refurbishment_cost">Refurb Cost</option>
                   <option value="note">Note</option>
                   <option disabled style="font-style:italic">--User-Defined-Fields--</option>
                   <option value="user_defined_fields__field_name">UDF Name</option>`
    }

    else if (type === 'build'){
        options = `<option value="build_number">Build Number</option>
                   <option value="assembly__name">Name</option>
                   <option value="assembly__assembly_type__name">Type</option>
                   <option value="assembly__description">Description</option>
                   <option value="created_at">Date Created</option>
                   <option value="updated_at">Date Modified</option>
                   <option value="build_notes">Notes</option>
                   <option value="detail">Detail</option>
                   <option value="is_deployed">is-deployed?</option>
                   <option value="time_at_sea">Time at Sea</option>
                   <option disabled style="font-style:italic">--Location--</option>
                   <option value="location__name">Name</option>
                   <option value="location__location_type">Type</option>
                   <option value="location__root_type">Root</option>`
    }

    else if (type === 'assembly'){
        options = `<option value="assembly_number">Number</option>
                   <option value="name">Name</option>
                   <option value="assembly_type__name">Type</option>
                   <option value="description">Description</option>`
    }

    for (let init_field of init_fields){
        options = options.replace('value="{{ opt }}"'.replace('{{ opt }}',init_field),
                                  'value="{{ opt }}" selected'.replace('{{ opt }}',init_field))
    }

    let lookup = `<select class="form-control col-md-3" id="qfield-lookup_c{{ cindex }}_f{{ findex }}" name="m{{ cindex }}_l{{ findex }}">
                    <option value="icontains">Contains</option>
                    <option value="exact">is-Exactly</option>
                    <option value="gte">Greater-Than or Equal</option>
                    <option value="lte">Less-Than or Equal</option>
                  </select>`
    lookup = lookup.replace('value="{{ opt }}"'.replace('{{ opt }}',init_lookup),
                            'value="{{ opt }}" selected'.replace('{{ opt }}',init_lookup))

    let query = `<input type="text" class="form-control col-md-4" id="field-query_c{{ cindex }}_f{{ findex }}" name="m{{ cindex }}_q{{ findex }}" value="{{ init_query }}">`
    query = query.replace('{{ init_query }}',init_query)

    var remove_button = `<button type='button' class="btn btn-primary-sm" href="#"
                      onclick="remove_row('{{ row_id }}');return false;" >
                      <i class="fa fa-minus"></i></button>`.replace("{{ row_id }}",row_id)

    row = row.replace('{{ options }}',options).replace('{{ lookup }}',lookup).replace('{{ query }}',query).replace('{{ minus_button }}',remove_button)
    row = row.replaceAll('{{ findex }}',row_index).replaceAll('{{ cindex }}',card_idx)
    return row
}

function remove_row(row_idx) {
    document.getElementById(row_idx).remove()
}

var prev_row_idx_percard = {}
function insert_row(card_idx,type){
    var card_id = 'qcard_c{{ cindex }}'.replace('{{ cindex }}',card_idx)
    ////var type_selector_id = 'model-select_c{{ cindex }}'.replace('{{ cindex }}',card_idx)
    //var type_selector_id = 'model-select'
    //var type_selector = document.getElementById(type_selector_id)
    var rows_div_id = 'fields_c{{ cindex }}'.replace('{{ cindex }}',card_idx)
    var rows_div = document.getElementById(rows_div_id)

    // prevents duplicate row indices from dynamically removed rows
    if (card_idx in prev_row_idx_percard){prev_row_idx_percard[card_idx] += 1}
    else {prev_row_idx_percard[card_idx] = rows_div.children.length}

    var new_row_index = prev_row_idx_percard[card_idx]
    var new_row = str2html(create_row(card_idx,type,new_row_index))
    rows_div.appendChild(new_row)
}

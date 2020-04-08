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


function create_card(card_name, model, card_data=null, fields=null){

    const card_id = 'qcard_c{{ cindex }}'
    let card_html = `<div class="card qcard mb-2" id="{{ card_id }}">{{ card_header }}{{ card_body }}</div>`.replace('{{ card_id }}',card_id)

    let card_header = `<div class="card-header container-fluid">
                         <div class="row">
                           <div class="col-md-10"><h4>Search Block {{ card_name }}</h4></div>
                           <div class="col-md-2 float-right">
                             <span class="pull-right clickable close-icon" data-effect="fadeOut" onclick="remove_elem('{{ card_id }}')"><i class="fa fa-times"></i></span>
                           </div>
                         </div>
                       </div>`.replace('{{ card_id }}',card_id).replace('{{ card_name }}',card_name)

    let card_body = `
      <div class="card-body">
        <div id="fields_c{{ cindex }}">
          {{ card_rows }}
        </div>
        {{ plus_button }}
      </div>`

    let card_rows = ''
    if (card_data){
        for (let row_idx in card_data['rows']){
            card_rows = card_rows+create_row(card_name,model,row_idx,card_data['rows'][row_idx],fields)
          }
    }
    else{
        card_rows = create_row(card_name,model,0,null, fields)
    }

    let plus_button = `<button type='button' class="btn btn-primary-sm" id="qfield_+ROW_c{{ cindex }}" href="#"
                      data-toggle="tooltip" title="Results for a card are filtered by ALL the rows"
                      onclick="insert_row(card_idx='{{ cindex }}',model='{{ model }}',field_options='globalhack');return false;" >
                      <i class="fa fa-plus"></i> ROW</button>`.replace('{{ model }}',model)
    //plus_button = plus_button.replace('{{ field_options }}',fields)
    card_body = card_body.replace('{{ card_rows }}',card_rows).replace('{{ plus_button }}',plus_button)
    card_html = card_html.replace('{{ card_header }}', card_header).replace('{{ card_body }}', card_body)
    card_html = card_html.replaceAll('{{ cindex }}',card_name)
    return card_html
}

function insert_card(model,card_data=null,fields=null){
    const cards = document.getElementById('adv-search-cards')
    let name = cards.children.length + 1
    if (card_data){ name = card_data['card_id'] }
    else if (name===1){name=''}
    const new_card = str2html(create_card(name,model,card_data,fields))
    cards.appendChild(new_card)
    enable_fancy_toggle(target_class='fancy-toggle--nega')
    $('[data-tooltip="tooltip"]').tooltip();
}

function change_select_multicity(id,size){
    const select_obj = $('#'+id)[0]
    if (size){
        select_obj.size=size
        select_obj.setAttribute('multiple','multiple')
    }
    else{
        select_obj.size=1
        select_obj.removeAttribute('multiple')
    }
    return true
}

function create_row(card_idx, model, row_index,row_data=null,field_options=null){
    let init_fields = []
    let init_lookup = 'icontains'
    let init_query = ''
    let init_nega = false
    let init_multi = false
    if (row_data){
        init_fields =  row_data['fields']
        init_lookup = row_data['lookup']
        init_query = row_data['query']
        init_nega = row_data['nega']
        init_multi = row_data['multi']
    }
    else{
        if (model === 'Inventory'){      init_fields = []   }
        else if (model === 'Part'){      init_fields = []   }
        else if (model === 'Build'){     init_fields = []   }
        else if (model === 'Assembly'){  init_fields = []   }
    }

    const row_id = "qfield-row_c{{ cindex }}_r{{ rindex }}"
    let row = `<div id="{{ row_id }}" class="form-group form-inline searchcard-row">
                 {{ nega }}{{ fields }}{{ lookup }}{{ query }}{{ minus_button }}</div>`
    row = row.replace("{{ row_id }}",row_id)

    const field_select_id = "field-select_c{{ cindex }}_r{{ rindex }}"
    let fields = `<div class="form-inline input-group col-md-5 px-1">
                      <div class="input-group-prepend">
                          <button class="btn btn-default input-group-text" type="button" data-toggle="dropdown" data-tooltip="tooltip" title="Results for a row will match the query against ANY of the selected fields">
                              <span class="fa fa-ellipsis-v"></span>
                              <ul class="dropdown-menu">
                                  <li><a class="dropdown-item" href="javascript:void(0)" onclick="change_select_multicity('{{ field_select_id }}',null)">Single</a></li>
                                  <li><a class="dropdown-item" href="javascript:void(0)" onclick="change_select_multicity('{{ field_select_id }}',6)">Multi 6</a></li>
                                  <li><a class="dropdown-item" href="javascript:void(0)" onclick="change_select_multicity('{{ field_select_id }}',12)">Multi 12</a></li>
                              </ul>
                           </select>
                       </div>
                       <select class="selectpicker form-control col-md-12 searchcard-row--fields"
                               id="{{ field_select_id }}"
                               name="f" {{ multi }}>
                           {{ options }}
                       </select>
                   </div>`
    if (init_multi) {
           fields = fields.replace('{{ multi }}', 'size=6 multiple')
    }else{ fields = fields.replace('{{ multi }}', 'size=1') }
    fields = fields.replaceAll('{{ field_select_id }}',field_select_id)

    let options = ''
    let option = ''
    if (field_options){ for (const field of field_options){
        if (field['disabled']){
            option = `<option disabled style="font-style:italic" >${ field['text'] }</option>`
        }
        else if ( init_fields.includes(field['value']) ){
            option = `<option selected value="${ field['value'] }">${ field['text'] }</option>`
        }
        else{
            option = `<option value="${ field['value'] }">${ field['text'] }</option>`
        }
        options = options + option
    }}
    options = options.replaceAll('value="','value="{{ cindex }}.{{ rindex }}.')
    fields = fields.replace('{{ options }}',options)

    let lookup_options = ''
    if (avail_lookups){for (const lookup of avail_lookups){
        if ( init_lookup === lookup['value'] ) {
            option = `<option selected value="${lookup['value']}">${lookup['text']}</option>`
        } else {
            option = `<option value="${lookup['value']}">${lookup['text']}</option>`
        }
        lookup_options = lookup_options + option
    }}
    let lookup = `<div class="form-inline col-md-2 px-1"><select class="form-control col-md-12 px-1 searchcard-row--lookup" id="qfield-lookup_c{{ cindex }}_r{{ rindex }}" name="l" >
                    ${lookup_options}
                  </select></div>`
    //lookup = lookup.replace('value="{{ opt }}"'.replace('{{ opt }}',init_lookup),
    //                        'value="{{ opt }}" selected'.replace('{{ opt }}',init_lookup))
    lookup = lookup.replaceAll('value="','value="{{ cindex }}.{{ rindex }}.')

    let query = `<div class="form-inline col-md-3 px-1 falseQ-textinput">
                     <input type="text" class="form-control col-md-12" id="field-query_c{{ cindex }}_r{{ rindex }}" value="{{ init_query }}">
                     <input type="hidden" id="field-hiddenquery_c{{ cindex }}_r{{ rindex }}" name="q" value="{{ cindex }}.{{ rindex }}.">
                 </div>`
    query = query.replace('{{ init_query }}',init_query)

    let remove_button = `<button type='button' class="btn btn-primary-sm float-right" href="#"
                      onclick="remove_elem('{{ row_id }}')" >
                      <i class="fa fa-minus"></i></button>`.replace("{{ row_id }}",row_id)

    let nega = `<input class="form-check-input fancy-toggle--nega" data-toggle="toggle" type="checkbox" id="qfield-nega_c{{ cindex }}_r{{ rindex }}" name="n" value="1">`
    if (init_nega === true){
        nega = nega.replace('value="1"','checked value="1"')}
    nega = nega.replace('value="','value="{{ cindex }}.{{ rindex }}.')

    row = row.replace('{{ fields }}',fields).replace('{{ lookup }}',lookup).replace('{{ query }}',query).replace('{{ minus_button }}',remove_button).replace('{{ nega }}',nega)
    row = row.replaceAll('{{ rindex }}',row_index).replaceAll('{{ cindex }}',card_idx)
    return row
}

function remove_elem(elem_id) {
    document.getElementById(elem_id).remove()
    return false;
}

const prev_row_idx_percard = {}
function insert_row(card_idx,model,field_options=null){
    const card_id = 'qcard_c{{ cindex }}'.replace('{{ cindex }}',card_idx)
    ////var type_selector_id = 'model-select_c{{ cindex }}'.replace('{{ cindex }}',card_idx)
    //var type_selector_id = 'model-select'
    //var type_selector = document.getElementById(type_selector_id)
    const rows_div_id = 'fields_c{{ cindex }}'.replace('{{ cindex }}',card_idx)
    const rows_div = document.getElementById(rows_div_id)

    // prevents duplicate row indices from dynamically removed rows
    if (card_idx in prev_row_idx_percard){prev_row_idx_percard[card_idx] += 1}
    else {prev_row_idx_percard[card_idx] = rows_div.children.length}

    // data objects can't be passed through button onclick functions, so here's a hack
    if (field_options === 'globalhack'){
        field_options = avail_fields   }

    const new_row_index = prev_row_idx_percard[card_idx]
    const new_row = str2html(create_row(card_idx,model,new_row_index,null,field_options))
    rows_div.appendChild(new_row)
    enable_fancy_toggle(target_class='fancy-toggle--nega')
    $('[data-tooltip="tooltip"]').tooltip();
}

function enable_fancy_toggle(target_class=null,target_id=null, toggle_kwargs=null){
    if (! toggle_kwargs){
        toggle_kwargs = { on: 'NOT', off: 'AND',
                          onstyle:'warning', offstyle:'outline-default',
                          size: 'mini', width:'50px'}
    }
    if (target_class){
        $('.'+target_class).each(function(){$(this).bootstrapToggle(toggle_kwargs)})
        }
    if (target_id){
        $('#'+target_id).bootstrapToggle(toggle_kwargs)
    }
}

function DoSubmit(){

    //TODO
    //field x lookup  validation
    // see searchcard-row, searchcard-row--fields, searchcard-row--lookup
    const rows = $('.searchcard-row')
    rows.each(function(){
        const row = $(this)
        const field_values = $(this).find('.searchcard-row--fields').val()
        const lookup_input = $(this).find('.searchcard-row--lookup')
        const lookup_value = lookup_input.val()
        console.log(field_values,lookup_value)
        //then match up the results of fields with avail_fields[idx]['value']
        //and make sure the lookup is in the corresponding avail_fields[idx]['legal_lookups']
        //for each field_value in field_values
        //idx = avail_fields.findIndex(f => f.value == field_value)
        //if ( avail_fields[idx].legal_lookups.includes(lookup_value) ){
        // do nothing, you're fine
        // }
        // else { set lookup_input to be red + set a flag to not-submit page}
        })

    //adding card and row info to query field responses
    const q_divs = $('.falseQ-textinput')
    q_divs.each(function(){
        const q_div = $(this).get(0)
        const visible_elem = q_div.firstElementChild
        const hidden_elem = q_div.lastElementChild
        hidden_elem.value = hidden_elem.value + visible_elem.value
    })

    return true
}

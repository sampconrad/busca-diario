import os
import fitz
import re
from unidecode import unidecode
import tkinter as tk
import PySimpleGUI as sg

root = tk.Tk()
root.withdraw()

def remove_accents(input_str):
    return unidecode(input_str)

def create_nomes_file(nomes_file_path):
   with open(nomes_file_path, 'a+', encoding='utf-8') as nomes_file:
       if not os.path.getsize(nomes_file_path):
           nomes_file.write('FULANO DE SOUZA, CICLANO DA SILVA, BELTRANO DOS SANTOS')
       nomes_content = nomes_file.read()
   return nomes_content

def read_names_from_file(names_file):
    with open(names_file, 'r', encoding='utf-8') as names_file:
        names = [name.strip() for name in names_file.read().split(',')]
    return names

def write_names_to_file(names, names_file):
    with open(names_file, 'w', encoding='utf-8') as names_file:
        names_file.write(', '.join(names))

def search_names_in_pdf(pdf_path, names):
    found_names = {name: [] for name in names}
    pdf_document = fitz.open(pdf_path)
    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        text = page.get_text()

        cleaned_text = re.sub(r'(\n|-)$', '', text.replace('\n', ' '))

        for name in names:
            normalized_name = remove_accents(name)
            if re.search(r'\b' + re.escape(normalized_name) + r'\b', remove_accents(cleaned_text), re.IGNORECASE):
                found_names[name].append(page_num + 1)

    pdf_document.close()
    return found_names

def main_window():
    sg.theme('Reddit')

    nomes_file_path = 'nomes.txt'
    if not os.path.exists(nomes_file_path):
        create_nomes_file(nomes_file_path)
    names = read_names_from_file(nomes_file_path)


    browse_btn = {'size':(20,1), 'button_color':("black","#00ffaa"), "font":("Arial", 10, "bold")}
    base_btn = {'size':(10,1), 'button_color':("black","#ffffff"), "font":("Arial", 10, "bold")}
    scan_btn = {'size':(20,2), 'button_color':("white","#F4564F"), "font":("Arial", 12, "bold")}

    layout = [
        [sg.Text('Diários selecionados:', font=("Arial", 12, "bold"), expand_x=True), sg.Input(key='-FILES-', enable_events=True, visible=False), sg.FilesBrowse('Carregar PDF Diário', **browse_btn, target='-FILES-', file_types=(("PDF Files", "*.pdf"),))],
        [sg.Listbox(values=[], key='-SELECTED_FILES-', size=(20, 5), expand_x=True)],
        [sg.Text('', size=(1, 1))],
        [sg.Text('Nomes a serem buscados:', font=("Arial", 12, "bold"), expand_x=True), sg.Button('Adicionar', **base_btn), sg.Button('Editar', **base_btn), sg.Button('Remover', **base_btn)],
        [sg.Listbox(values=names, key='-NAMES-', size=(20, 20), expand_x=True, enable_events=True)],
        [sg.Text('', size=(1, 1))],
        [sg.Button('Buscar', **scan_btn, expand_x=True)],
        [sg.ProgressBar(max_value=100, orientation='h', size=(20, 20), key='progress', expand_x=True)],
    ]

    window = sg.Window('Busca Diario', layout, finalize=True, size=(700, 650))

    while True:
        event, values = window.read()

        
        if event == sg.WINDOW_CLOSED:
            break 
        elif event == 'Buscar':
            pdf_files = values['-FILES-'].split(';')
            selected_files = values['-SELECTED_FILES-']
            scan_and_display_results(pdf_files, names, window)
        elif event == 'Adicionar':
            new_name = sg.popup_get_text('Digite um novo nome:')
            if new_name:
                names.append(new_name.strip())
                window['-NAMES-'].update(values=names)
                write_names_to_file(names, nomes_file_path)
        elif event == 'Editar':
            selected_name = values['-NAMES-'][0] if values['-NAMES-'] else None
            if selected_name:
                edited_name = sg.popup_get_text('Edite o nome:', default_text=selected_name)
                if edited_name:
                    names[names.index(selected_name)] = edited_name.strip()
                    window['-NAMES-'].update(values=names)
                    write_names_to_file(names, nomes_file_path)
        elif event == 'Remover':
            selected_name = values['-NAMES-'][0] if values['-NAMES-'] else None
            if selected_name and sg.popup_yes_no(f'Remover {selected_name}?') == 'Yes':
                names.remove(selected_name)
                window['-NAMES-'].update(values=names)
                write_names_to_file(names, nomes_file_path)

        if '-FILES-' in values:
            selected_files = values['-FILES-'].split(';')
            window['-SELECTED_FILES-'].update(values=selected_files)

    window.close()

def scan_and_display_results(pdf_files, names, window):
   results = {}
   progress_bar = window['progress']
   total_files = len(pdf_files)
   
   window['Buscar'].update(disabled=True, button_color=("#F4564F","white"))
   for i, pdf_file in enumerate(pdf_files):
       found_names = search_names_in_pdf(pdf_file, names)
       results[pdf_file] = found_names
       progress = (i + 1) / total_files * 100
       progress_bar.UpdateBar(progress)
    
   window['Buscar'].update(disabled=False, button_color=("white","#F4564F"))

   progress_bar.UpdateBar(0)
   display_results(results)


def display_results(results):
  result_text = ''
  for pdf_file, found_names_dict in results.items():
      result_text += f'___________________________\nDiario:  {pdf_file}\n'
      for name, page_numbers in found_names_dict.items():
          if page_numbers:
              result_text += f' {name} -  Pág. {", ".join(map(str, page_numbers))}\n'
      result_text += '\n'

  layout = [
      [sg.Multiline(result_text, size=(80, 30))],
  ]

  window = sg.Window('Resultados da Busca', layout, finalize=True)

  while True:
      event, values = window.read()
      if event == sg.WINDOW_CLOSED:
          break

  window.close()


if __name__ == '__main__':
    main_window()
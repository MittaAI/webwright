   with open(file_path, 'r', encoding=encoding) as file:
       return file.read()
   with open(file_path, 'w', encoding='utf-8') as file:
       file.write(content)
   content = read_file(file_path, encoding='utf-8')
   print(content)

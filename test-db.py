import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
db = MySQLdb.connect("35.185.88.63" , "root" , "admin")
cur = db.cursor()
cur.execute("use easytodb")
cur.execute("SELECT COUNT(*) FROM reestr")

for row in cur.fetchall():
    print(row)

db.close()


##АІ4639НТ\r


def convert_csv():
    with open('C:\\Users\\Dmytro_Mazniev\\Documents\\GitHub\\etc\\tz_opendata_z01012013_po31122013.csv', encoding="utf8") as f:
        content = f.readlines()
    writer = []

    with open('C:\\Users\\Dmytro_Mazniev\\Documents\\GitHub\\etc\\tz_opendata_z01012013_po31122013_F.csv', 'w', encoding="utf8") as f:
        for line in content:
            new_line = line.replace('"','')
            new_line = new_line.replace('\n','')
            new_line_list = new_line.split(';')
            text = ''
            text += new_line_list[0] + ","
            for i in range(1,len(new_line_list)-1):
                text += '"' + new_line_list[i] + '"' + ","
            text += new_line_list[len(new_line_list)-1] + "\n"
            f.write(text)

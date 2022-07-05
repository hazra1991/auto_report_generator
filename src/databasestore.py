import sqlite3
import psycopg2

from typing import Any


#########################################################################################
# TODO need to remove this 

temp_conn_drive={
    "sqlite3":sqlite3,
    "postgress":psycopg2
}
############################################################################################

class DBConnect:
    def __init__(self,config):
        self.conn = None

        if "sqlite3_db_name" in config:
            self.conn = temp_conn_drive["sqlite3"].connect(config['sqlite3_db_name'])
        else:
            self.conn = temp_conn_drive["postgress"].connect(**config)

        self.curr = self.conn.cursor()
    
    def execute_query(self,query,*args):
        # print(query)
        self.curr.execute(query,*args)
        self.conn.commit()
        return self

    
    def fetch_results(self):
        return self.curr.fetchall()

    
    def csv_to_db(self):
        pass
    
    def __del__(self):
        if self.conn:
            self.conn.close()



class Field:
    def __init__(self, name, column_type,primary_key=False):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__dict__})"


class StringField(Field):

    def __init__(self, name,**kw):
        super().__init__(name, 'TEXT',**kw)


class IntegerField(Field):
    def __init__(self, name,**kw):
        super().__init__(name, 'BIGINT',**kw)


class recType(type):
    def __new__(cls,name,base,dc):
        dc["__table__"] = name
        dc["__columns__"] = [col for col,val in dc.items() if isinstance(val,Field)]
        dc["__mapping__"]= {col:dc[col] for col in dc["__columns__"] }
        return super().__new__(cls,name,base,dc)


class Model(metaclass=recType):
    def __init__(self):
        try:
            if not isinstance(self.__db_conn_obj__,DBConnect):
                raise AttributeError(f"'set_database_connector_object'  not called on the model {self.__table__}")
        except AttributeError as e:
            raise AttributeError(f"'set_database_connector_object'  not called on the model {self.__table__}")

    def save(self):
        params = [f"'{self.__dict__[col]}'" for col in self.__columns__]
        q= f"INSERT INTO {self.__table__} VALUES ({','.join(params)})"
        print(q)

        rs = self.__db_conn_obj__.execute_query(q)
        return

    def update(self,where='',eq=''):
        params = [f"{col} = '{self.__dict__[col]}'" for col in self.__columns__]

        q = f"UPDATE {self.__table__} SET {','.join(params)} WHERE {where} = '{eq}'" 

        print(q)
        self.__db_conn_obj__.execute_query(q)

    @classmethod
    def fetch_details(cls,where=None, eq:list[str]=None):
        if eq is not None and not isinstance(eq,list):
            raise ValueError("kindly Valid arguments for the functions should be a list of strings")
        
        # if not where and not eq:
        #     q= f"SELECT * FROM {cls.__table__}"
        #     records = cls.__db_conn_obj__.execute_query(q).fetch_results()
        #     print("recs ======================dkjsabdasjkdbajskdbakjsdbaskj========",records)
        #     return

        join_param = [f"'{x}'" for x in eq]
        if len(eq) == 1:
            q= f"SELECT * FROM {cls.__table__} WHERE {where} = {join_param[0]}"
        else:
            q = f"SELECT * FROM {cls.__table__} WHERE {where} IN ({','.join(join_param)})"
        records = cls.__db_conn_obj__.execute_query(q).fetch_results()
        print("recs ==============================",records)
        rec_list = []
        for record in records:
            m = {}
            for index in range(len(cls.__columns__)):
                m[cls.__columns__[index]] = record[index]
            rec_list.append(m)
        
        return rec_list


    def __setattr__(self, __name: str, __value: Any) -> None:

        if not __name in self.__columns__:
            raise AttributeError(f"Given name '{__name}' is not defined in the model '{self.__class__.__name__}'")
        return super().__setattr__(__name, __value)


    @classmethod
    def createTable_if_not_exists(cls):
        params = []
        for col in cls.__columns__:
            mp = cls.__mapping__[col]
            string = f"{mp.name} {mp.column_type}"
            if mp.primary_key:
                string = string + " PRIMARY KEY"
            params.append(string)

        join_column = ','.join(params)
        q = f"""CREATE TABLE IF NOT EXISTS {cls.__table__} 
            ({join_column});"""

        cls.__db_conn_obj__.execute_query(q)

    @classmethod
    def migrate_and_alter_table(cls):
        print("migrate not impolemented contact ADMIN")

    
    @classmethod
    def set_database_connector_object(cls,conn_obj):
        """ need to get call to set the connection object before creating records """
        cls.__db_conn_obj__ = conn_obj


    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__dict__})"


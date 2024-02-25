import requests, json, os
from BaiduTrans import BaiduTrans

class WordDefinition:
    def __init__(self, word):
        self.word = word
        self.get_data()
        self.process_results()
        self.file_dir = r'.\vocabulary\save\cache'
        self.file_path = os.path.join(self.file_dir, self.word+'.txt')
    
    def request_api(self):
        url = "https://wordsapiv1.p.rapidapi.com/words/"+self.word
        headers = {
            # get headers at https://www.wordsapi.com/
        }
        self.datapack = requests.get(url, headers=headers)
        self.data = self.datapack.json()
    
    def get_data(self):
        self.file_dir = r'.\vocabulary\save\cache'
        self.file_path = os.path.join(self.file_dir, self.word+'.txt')
        if not os.path.exists(self.file_dir): # 初始化创建路径
            os.makedirs(self.file_dir)
        if os.path.exists(self.file_path): # 缓存中有数据
            with open(self.file_path,'r') as f:
                self.data = json.loads(f.read())
        else: # 缓存中没有数据
            self.request_api()
            bd_result = BaiduTrans(self.word) # 百度的api
            bd_cn_str = ''
            for i in bd_result['trans_result']:
                bd_cn_str = bd_cn_str+';'+(i['dst'])
            if self.get_data_staus(): # 返回成功才写入缓存
                self.data['cntrans'] = bd_cn_str.strip(';')
                with open(self.file_path,'w') as f: # 存入缓存
                    f.write(json.dumps(self.data))
                return self.data
    
    def get_data_staus(self): # 返回成功为true，否则false
        return self.datapack.status_code in {200,'200'}
    
    def process_data(self):
        self.results = self.data.get('results')
        self.syllables = self.data.get('syllables')
        self.pronunciation = self.data.get('pronunciation')
        self.chinese = self.data.get('cntrans')
        if self.syllables:
            self.syllables = self.syllables.get('list')
        if self.pronunciation and not isinstance(self.pronunciation, str):
            self.pronunciation = self.pronunciation.get('all')
    
    def process_results(self):
        def format_list(lst): # 格式化词条中的列表
            return str(lst).replace('[', '').replace(']', '').replace("'", '')
        self.process_data()
        self.chinese_only = ['中文：'+self.chinese]
        self.outcome = ['中文：'+self.chinese]
        self.outcome.append('发音：%s | 音节：%s' % (self.pronunciation, self.syllables))
        if self.results:
            for i, obj in enumerate(self.results):
                index = i + 1
                definition = obj.get('definition')
                partOfSpeech = obj.get('partOfSpeech')
                synonyms = format_list(obj.get('synonyms'))
                derivation = format_list(obj.get('derivation'))
                examples = format_list(obj.get('examples'))
                verbGroup = obj.get('verbGroup') # 暂时无用
                hasTypes = obj.get('hasTypes')   # 同上
                in_format = '%s (%s) - %s 释义：%s | 近义：%s | 衍生：%s | 例句：%s' % (
                    self.word,index,partOfSpeech,definition,synonyms,derivation,examples
                    )
                self.outcome.append(in_format)
        self.iterate()
    
    def alter_cn_result(self, new_result):
        self.get_data()
        self.data['cntrans'] = new_result
        with open(self.file_path,'w') as f:
            f.write(json.dumps(self.data))

    def iterate(self):
        self.publish = ''
        for i in self.outcome:
            self.publish = self.publish+'\n'+i
        self.publish = self.publish.strip()

if __name__ == '__main__':
    w = WordDefinition('abstract')
    print(w.publish)

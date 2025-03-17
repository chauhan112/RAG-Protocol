import dill as pickle
import gzip
class CompressDB:
    def content():
        class Temp:
            def compressToBinVal(content):
                return gzip.compress(content)
            def decompressFromBinVal(content):
                return gzip.decompress(content)
        return Temp
class SerializationDB:
    def pickleOut(dataStructure, outFileName):
        data = pickle.dumps(dataStructure)
        dataCompressed = CompressDB.content().compressToBinVal(data)
        with open(outFileName, "wb") as f:
            f.write(dataCompressed)
    def readPickle(filePath):
        with open(filePath, "rb") as f:
            binValCompressed = f.read()
        try:
            binVal = CompressDB.content().decompressFromBinVal(binValCompressed)
        except:
            binVal = binValCompressed
        return pickle.loads(binVal)
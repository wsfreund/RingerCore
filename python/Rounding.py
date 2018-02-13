__all__ = ['roundingLogger', 'truncate', 'pdgRound', 'reducePowerOf10Str']

from RingerCore.Logger import Logger

_mLogger = Logger.getModuleLogger(__name__)
roundingLogger = _mLogger

def truncate( number, p, retInt=False ):
    p = 10. ** ( p )
    ret = int( number * p ) / p
    if retInt: ret = int(ret)
    return ret

def pdgRound( number, trunc_pos = None, fill = '0', digits=None, getOrder = False ):
    # First we check whether we are rounding number with a possible uncertainty:
    if isinstance(number,(list,tuple)):
        if len(number) == 1:
            # Just to increase code flexibility
            return pdgRound(number[0], fill = fill, digits=digits, getOrder = getOrder)
        elif len(number) > 2:
            # TODO We can use this in case systematic uncertainties are provided
            raise NotImplementedError("This version cannot handle systematic.")
        # Deal with statistic uncertainty
        if number[1] is None:
            return pdgRound(number[0], trunc_pos = trunc_pos, fill = fill, digits=digits, getOrder = getOrder)
        rms, trunc_pos = pdgRound(number[1], trunc_pos = trunc_pos, fill = fill, digits=digits, getOrder = True)
        _mLogger.verbose("====================================================")
        mean = pdgRound(number[0], trunc_pos = trunc_pos, fill = fill, digits=digits)
        return (mean, rms) if not getOrder else ((mean, rms), trunc_pos)
    # We now are handling single number rounding:
    # In case number is zero, then return zero:
    if number == 0: return '0' if not getOrder else ('0', 0)
    # If number is lower than zero, calculate rounding on positive number and
    # then adds negative sign on it:
    if number < 0: 
        if not getOrder:
            return '-' + pdgRound(-number, trunc_pos=trunc_pos, fill=fill, digits=digits) 
        else:
            number, trunc_pos = pdgRound(-number, trunc_pos=trunc_pos,fill=fill, digits=digits,getOrder=True) 
            return '-' + number, trunc_pos
    # Keep track of the number "true" first significant digit
    import math
    first_significant_digit_order = int(math.floor(math.log10(number)))
    if digits is not None:
        if digits <= 0:
            raise ValueError("Illegal value for digits (%d)" % digits, digits)
        if trunc_pos is None:
            round_pos = digits - ( first_significant_digit_order + 1 )
        else:
            digits = first_significant_digit_order + 1 - trunc_pos
            round_pos = - trunc_pos
        _mLogger.verbose('Rounding at position %d, digits:%s, number:%s', round_pos, digits, number)
        # We simply return the number rounded 
        ret = round( number, round_pos )
        added_new_digits = ( ( number / ( 10.**first_significant_digit_order) ) % 10. ) > float('9.' + '9' * (digits-1) + '5')
        trunc_pos = - round_pos + added_new_digits
        _mLogger.verbose('Rounded number:%s, trunc_pos was %d (added_new_digits:%s)', ret, trunc_pos, added_new_digits)
        if digits + added_new_digits <= 0: digits = 1
        if trunc_pos >= 0:
            ret = str(int(ret))[:digits + added_new_digits] + fill * ( first_significant_digit_order - digits + 1 )
        else:
            ret = str(ret)
        #if digits - trunc_pos >= 0:
        return ( (ret, trunc_pos) if getOrder else ret )
    else:
        # This is a bit tricky as the truncation position may be given by the user
        # and differ from the study case where the digits around the first
        # significant digit are used. We handle this by two cases as follow:
        if trunc_pos is not None: 
            trunc_pos = int(trunc_pos)
            ret_trunc_pos = trunc_pos
            no_digits_lower_than_trunc_pos = True
        else:
            trunc_pos = first_significant_digit_order
            ret_trunc_pos = None
            no_digits_lower_than_trunc_pos = False
        # APPLY PDG Rounding 
        # The basic rule states that if the three highest order digits of the error
        # lie between 100 and 354, we round to two significant digits. If they lie
        # between 355 and 949, we round to one significant digit. Finally, if they
        # lie between 950 and 999, we round up to 1000 and keep two significant
        # digits. In all cases, the central value is given with a precision that
        # matches that of the error. Rounding is not performed if a result in a
        # Summary Table comes from a single measurement, without any averaging.
        # Note that, even for a single measurement, when we combine statistical and
        # systematic errors in quadrature, rounding rules apply to the result of
        # the combination. 
        # We get the base to calculate how many digits we will keep
        base = ( number / ( 10 ** ( trunc_pos - 2 ) ) ) % 1000.
        _mLogger.verbose( "input:%s|base:%s|trunc_pos:%s",number,base,trunc_pos)
        if no_digits_lower_than_trunc_pos:
            # When trunc_pos is given by the user, we want to keep only this digit.
            # In order to allow that this is also evaluated by the PDG standard
            # rounding procedure bellow, we simply round the number so that the
            # evaluated base consists only of its order of hundreds.
            base = int(('%03d' % round(base,-2)))
            if base == 1000:
                # In case it reachs a thousand, we move trunc_pos one digit ahead
                # and recalculate the base at that pos, keeping only two digits of
                # precision
                number += 10 ** (trunc_pos)
                base = 0
            _mLogger.verbose( "Modified base due to no_digits_lower_than_trunc_pos, base:%s|trunc_pos:%s",base,trunc_pos)
        if base < 100 or ( base == 100 and first_significant_digit_order < trunc_pos ): 
            _mLogger.verbose("le 100 or keeping only one significant digit")
            # Although this is not explicitly specified in the PDG text (since it
            # does not account how to deal with uncertainties greater than the
            # central value), ATLAS paper on rounding numbers shows cases where the
            # number is rounded to the nearest integer in that truncation position.
            base = ('%03d' % round(base,-2))[0] 
        elif 100 <= base <= 354:
            _mLogger.verbose("keeping two digits")
            # two digits
            if ret_trunc_pos is None: ret_trunc_pos = trunc_pos - 1
            base = ('%03d' % int(round(base,-1)))[:2]
            if trunc_pos >= 2: base += fill
        elif 354 < base <= 949:
            _mLogger.verbose("keeping one digit")
            # one digit
            if ret_trunc_pos is None: ret_trunc_pos = trunc_pos
            base = ('%03d' % int(round(base,-2)))[:1]
            if trunc_pos >= 2: base += 2*fill
            elif trunc_pos == 1: base += fill
        else: # 949 < base < 999:
            import re
            _mLogger.verbose("keeping two digits and increasing trunc_pos")
            number = ( '' if first_significant_digit_order <= trunc_pos 
                        else re.sub(('\d{%d}$' % ( trunc_pos + 1)),'',str(truncate(number, -(trunc_pos), retInt = True))) )
            # trunc_pos
            if ret_trunc_pos is None: ret_trunc_pos = trunc_pos
            if trunc_pos >= 2:
                ret = number + '10' + fill * trunc_pos
            elif trunc_pos >= -1:
                ret = number + ( '10' if trunc_pos == 0 else '1.0' )
            else:
                if not number:
                    ret = '0.' + fill * ( -trunc_pos - 2 ) + '10'
                else:
                    ret = str(round(number,trunc_pos)) + '10'
            return ( (ret, ret_trunc_pos) if getOrder else ret )
        if no_digits_lower_than_trunc_pos and first_significant_digit_order > trunc_pos:
            # We need to ensure that our base keeps the amount of digits that it can maintain
            delta = first_significant_digit_order - trunc_pos + 1
            _mLogger.verbose("delta: %s, first_significant_digit_order: %s, trunc_pos: %s", delta, first_significant_digit_order, trunc_pos)
            if trunc_pos < 0:
                base = base[0]
                _mLogger.verbose("Modified base due to no_digits_lower_than_trunc_pos: %s", base)
            elif trunc_pos <= 2:
                base = base[0] + fill * trunc_pos
                _mLogger.verbose("Modified base due to no_digits_lower_than_trunc_pos: %s", base)
    import re
    if trunc_pos >= 2:
        _mLogger.verbose("trunc_pos >= 2")
        number = '%d' % number
        ret = re.sub('\d{%d}$' % (trunc_pos + 1), base + fill * (trunc_pos - 2), number )
    elif 0 <= trunc_pos < 2:
        _mLogger.verbose("0 <= trunc_pos < 2")
        number = ( '' if first_significant_digit_order <= trunc_pos 
                    else re.sub(('\d{%d}$' % ( trunc_pos + 1)),'',str(truncate(number, -(trunc_pos+1), retInt = True))) )
        diff = trunc_pos + 1 - len(base)
        ret = number + (base[:diff] + '.' + base[diff:] if diff < 0 else base)
    else:
        _mLogger.verbose("trunc_pos < 0")
        number = '' if first_significant_digit_order <= trunc_pos else str(truncate(number, -(trunc_pos+1), retInt = trunc_pos==-1))
        if first_significant_digit_order > trunc_pos and -trunc_pos-1 == 0: number += '.'
        if not number:
            ret = '0.' + fill * ( -trunc_pos - 1 ) + base
        else:
            ret = number + base
    return ( (ret, ret_trunc_pos) if getOrder else ret )

def reducePowerOf10Str(s, doPrint = False):
  import re
  if isinstance(s,(list,tuple)): 
    return map(reducePowerOf10Str, s)
  if isinstance(s,(float,int)): s = pdgRound(s)
  if not isinstance(s,basestring): return s
  thousand = re.compile(r"""
    (?<!\S)
    # Ensures that we are at the begin of a word
    ###############################################
    (?=(\d+|\d*,?(\d{3},)*\d+)k*|(k*\.^))
    # Guarantees that what come next is a sequence of digits or commas ending
    # with possible 'k's added from previous substitutions
    ###############################################
    (?P<BEFORE>(\d+|\d*,?(\d{3},)*\d+))
    # What may come before the matching pattern that we want to substitute
    # (000). It is basically the string the we have guaranteed before, except
    # for the 'k*' that we will use later on
    ###############################################
    (,?0{3})(?!(\d|,)+)
    # This is the match that we will change by k. It must not be followed by a
    # digit or a comma to ensure that we are substituting the last three zeros
    # available. We also consume a left comma if available
    ###############################################
    (?:\.?(?!\d+))
    # And finally, we also consume an ending dot if it hasn't following
    # digits. It will also consume end of sentence punctuation
    ###############################################
    (?P<AFTER>(k*)|(k*\.^))
    # To ensure that the string will keep any already available 'k's
    """
      , re.X)
  s2 = thousand.sub(r'\g<BEFORE>k\g<AFTER>',s)
  while s2 != s:
    s = s2
    s2 = thousand.sub(r'\g<BEFORE>k\g<AFTER>',s)
  s = re.sub(r'k\.?k|kk','M',s2)
  s = re.sub(r'Mk|kM|kkk','B',s)
  s = re.sub(r'MM|kB|Bk|kkkk','T',s)
  s = re.sub(r'kT|Tk|kkkkk','P',s)
  return s



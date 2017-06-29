#(0..2**16).each { |num| print (if num > 2**15 then 0 else 2* num end).to_s + " " }
#(0..2**16).each { |num| print (if num > 10000 and num != 20000 then 0 else num end).to_s + " " }
#(0..2**16).each { |num| print (if num > 10000 and num != 20000 then 0 else (num*2**16/10000) end).to_s + " " }
# (0..2**16).each { |num| print (if num > 5000 then (if num <= 16000 or num == 20000 then 65535 else 0 end) else (num*(2**16)/5000) end).to_s + " " }

lowpass = 345
boost_amount = 400
boost_end = 1100

def calc(x)
  amplitude = 65535.0
  sharpness = 2048.0

  (amplitude*(1.0-1.0/(1.0+x.to_f/sharpness))).to_i
end
#
# (0..2**16).each { |num| print (if num > 20000 then 0 else calc(num) end).to_s + " " }


#(0..255).each { |num| print (if num > 10 and num < 61 then num+10 else num end).to_s + " " }
#(0..2**16).each { |num| print (if num > 10000 then (if num == 20000 then 10000 else 0 end) else (if num < lowpass then 0 else (if num < boost_end then num+400 else num end) end) end).to_s + " " }
#(0..2**16).each { |num| print (if num > 10000 then (if num == 20000 then 10000 else 0 end) else (if num < lowpass then 0 else (if num < boost_end then num else num end) end) end).to_s + " " }

def adjust(x)
  x = if x > 10000 then 10000 else x end
  (x.to_f*(2**16-1)/10000).to_i
end

#(0..2**16).each { |num| print (if num > 10000 then (if num == 20000 then 65535 else 0 end) else (if num < lowpass then 0 else (if num < boost_end then adjust(num+400) else adjust(num) end) end) end).to_s + " " }

(0..2**16).each { |num| print (if num > 16000 then (if num == 20000 then 65535 else 0 end) else (if num < lowpass then 0 else (if num < boost_end then calc(num) else calc(num) end) end) end).to_s + " " }
#(0..2**16).each { |num| print (if num > 16000 then (if num == 20000 then 65535 else 0 end) else (if num < lowpass then 0 else (if num < boost_end then calc(num+boost_amount) else calc(num) end) end) end).to_s + " " }

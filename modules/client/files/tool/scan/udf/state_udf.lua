local function filter_clist(clist)
	--debug("[ENTER: cz] <%s>  Value(%s) valType(%s)", "filter_cid:", tostring(clist), type(clist))
	return function(record)
		for idx=1, list.size(clist), 1 do
			if record.cawlEgId == clist[idx] then
				debug("[ENTER: cz] <%s>  Value(%s) valType(%s)", "filter_cid: matched", tostring(clist[idx]), type(clist[idx]))
				return true
			end
		end
		return false
	end
end
local function filter_crange(start, stop)
	return function(record)
		return record.cawlEgId >= start and record.cawlEgId < stop
	end
end
local function map_assign(rec)
	return map{ skey=rec.skey, cawlEgId=rec.cawlEgId, gen=record.gen(rec) }
end
function multifilters(stream, start, stop)
	local my_filter = filter_crange(start, stop)
	return stream:filter(my_filter):map(map_assign)
end


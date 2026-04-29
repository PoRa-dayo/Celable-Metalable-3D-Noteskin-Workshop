local t = Def.Model {
	Meshes="_mine meshes.txt";
	Materials="_mine materials 4th.txt";
	Bones="_mine bones.txt";
    InitCommand=function(self)
		self:basezoomx(0.8):basezoomy(0.8)
    end;
};

return t;

